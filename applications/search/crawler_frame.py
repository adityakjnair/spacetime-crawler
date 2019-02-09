import logging
from datamodel.search.Adityan1MonishppSkanade1_datamodel import Adityan1MonishppSkanade1Link, OneAdityan1MonishppSkanade1UnProcessedLink
from spacetime.client.IApplication import IApplication
from spacetime.client.declarations import Producer, GetterSetter, Getter
import lxml.html
import re, os
from time import time
from urlparse import urlparse, parse_qs, urljoin

from tld import get_tld
from tld.utils import update_tld_names

logger = logging.getLogger(__name__)
LOG_HEADER = "[CRAWLER]"


max_link = None
max_link_count = 0

highest_count = 0
highest_count_link = None

@Producer(Adityan1MonishppSkanade1Link)
@GetterSetter(OneAdityan1MonishppSkanade1UnProcessedLink)
class CrawlerFrame(IApplication):
    app_id = "Adityan1MonishppSkanade1"

    def __init__(self, frame):
        self.app_id = "Adityan1MonishppSkanade1"
        self.frame = frame
        self.starttime = time()


    def initialize(self):
        self.count = 0
        links = self.frame.get_new(OneAdityan1MonishppSkanade1UnProcessedLink)
        if len(links) > 0:
            print "Resuming from the previous state."
            self.download_links(links)
            update_tld_names()
        else:
            l = Adityan1MonishppSkanade1Link("http://www.ics.uci.edu/")
            print l.full_url
            self.frame.add(l)

    def update(self):
        unprocessed_links = self.frame.get_new(OneAdityan1MonishppSkanade1UnProcessedLink)
        if unprocessed_links:
            self.download_links(unprocessed_links)

    def download_links(self, unprocessed_links):
        global highest_count
        global highest_count_link
        f = open("highestcount.txt", "w")
        f1 = open("subdomaincount.txt", "w")        
        for link in unprocessed_links:
            print "Got a link to download:", link.full_url
            downloaded = link.download()
            links = extract_next_links(downloaded)
            count=0
            for l in links:
                if is_valid(l):
                    count+=1
                    analyze_link(l)
                    self.frame.add(Adityan1MonishppSkanade1Link(l))
            if count>highest_count:
                highest_count=count
                highest_count_link=link.full_url
        
        f.write('Link with highest count: '+str(highest_count_link))
        f.write('Count: '+str(highest_count))
        for key in subdomain_map.keys():
            f1.write(str(key)+' = '+str(subdomain_map[key])+'\n')
        f.close()
        f1.close()

    def shutdown(self):
        print (
            "Time time spent this session: ",
            time() - self.starttime, " seconds.")
    
def extract_next_links(rawDataObj):
    outputLinks = []
    '''
    rawDataObj is an object of type UrlResponse declared at L20-30
    datamodel/search/server_datamodel.py
    the return of this function should be a list of urls in their absolute form
    Validation of link via is_valid function is done later (see line 42).
    It is not required to remove duplicates that have already been downloaded. 
    The frontier takes care of that.
    
    Suggested library: lxml
    '''

    global max_link
    global max_link_count
    
    # If object has content, extract links from content
    if rawDataObj.content:

        # Convert string to HTML object
        html = lxml.html.fromstring(rawDataObj.content)
        link_count = 0
        # Loop through links in HTML object
        for l in html.iterlinks():
            url = l[2]  # l: (element, attribute, link, pos)

            # break up chained together URLs,
            # sometimes paths looked like this: www.ics.uci.edu//ugrad/policies/Add_Drop_ChangeOption.php/about/QA_Petitions.php/
            # where multiple paths were concatenated together.
            all_urls = re.findall(r'([^:]*?[^:\/]*?\.[^:\/]*?(?:\/|$))',url) # [1:] because ics.uci.edu will be element 0
            
            if len(all_urls) > 1:
                if all_urls[0][:2] == '//': all_urls[0] = all_urls[0][2:]; #cleaning up regex problem
                all_urls = [all_urls[0] + ('/' if all_urls[0][-1] != '/' else '') + p for p in all_urls[1:]] #make not relative
            else:
                all_urls = [url]

            for r_url in all_urls:
                abs_url = r_url

                # If link is not absolute, add host name
                if not urlparse(abs_url).netloc:  # scheme://netloc/path;parameters?query#fragment

                    # If webpage was redirected, use final_url as host name
                    if rawDataObj.is_redirected:
                        host = rawDataObj.final_url
                    # Otherwise, just use url as host name
                    else:
                        host = rawDataObj.url

                    # Make link absolute
                    abs_url = urljoin(host, abs_url)

                # Add to output list
                outputLinks.append(abs_url)
                link_count += 1

        # Analytics: Keep track of page with most out links
        if link_count > max_link_count:
            max_link = host
            max_link_count = link_count

    # Print final result (comment out later)
    # for link in outputLinks:
    #     print(link)

    return outputLinks

subdomain_map = {}
def analyze_link(url):
    global subdomain_map
    parsed = urlparse(url)
    uri = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed)
    obj = get_tld(uri, as_object=True)
    subdomain = str(obj.subdomain+'.'+obj.fld)
    if subdomain in subdomain_map.keys():
        subdomain_map[subdomain] += 1
    else:
        subdomain_map[subdomain] = 1

    # print('Path:',parsed.path)
    # print('Query:',parsed.query)

already_seen = set()
def is_valid(url):
    '''
    Function returns True or False based on whether the url has to be
    downloaded or not.
    Robot rules and duplication rules are checked separately.
    This is a great place to filter out crawler traps.
    '''
    url = url.lower()

    if 'mailto' in url:
        return False # we can easily ignore mail urls

    if '#' in url:
        url = url[10:url.rfind('#')] # we don't realy care aboute what position to start at in the page

    global already_seen
    if url in already_seen:
        return False
    already_seen.add(url)

    parsed = urlparse(url)

    #heuristic: odd urls had concatenated multiple urls together
    fullpath = parsed.path + parsed.query + parsed.params
    if re.search(r'https?://',fullpath):
        return False

    repetitions = re.finditer(r'(.+?)\1+',fullpath) #get any repeptitions in the string
    for rep in repetitions:
        if len(rep.group(1)) >= 5: #only care about long repeating terms (cant be too small or words like off will trigger...)
            return False

    # heuristic: if there are a lot of parameters it is possibly risky dynamically generated content like calendar.ics.uci.edu
    param_slack = 3
    if len(parse_qs(parsed.query)) >= param_slack:
        return False

    if parsed.scheme not in set(["http", "https"]):
        return False

    try:
        return ".ics.uci.edu" in parsed.hostname \
            and not re.match(".*\.(css|js|bmp|gif|jpe?g|ico" + "|png|tiff?|mid|mp2|mp3|mp4" \
                            + "|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf" \
                            + "|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso|epub|dll|cnf|tgz|sha1" \
                            + "|thmx|mso|arff|rtf|jar|csv" \
                            + "|rm|smil|wmv|swf|wma|zip|rar|gz" \
                            + "|lif)$", parsed.path.lower())
    except TypeError:
        print ("TypeError for ", parsed)

