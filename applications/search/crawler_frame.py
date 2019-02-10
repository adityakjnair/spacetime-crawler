import logging
from datamodel.search.Adityan1MonishppSkanade1_datamodel import Adityan1MonishppSkanade1Link, OneAdityan1MonishppSkanade1UnProcessedLink
from spacetime.client.IApplication import IApplication
from spacetime.client.declarations import Producer, GetterSetter, Getter
import lxml.html
import re
import os
from time import time
from urlparse import urlparse, parse_qs, urljoin

from tld import get_tld
from tld.utils import update_tld_names

logger = logging.getLogger(__name__)
LOG_HEADER = "[CRAWLER]"


largest_link = None
largest_number_of_links = 0

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
            update_tld_names()
            self.frame.add(l)

    def update(self):
        unprocessed_links = self.frame.get_new(
            OneAdityan1MonishppSkanade1UnProcessedLink)
        if unprocessed_links:
            self.download_links(unprocessed_links)

    def download_links(self, unprocessed_links):
        global highest_count
        global highest_count_link
        f = open("analytics.txt", "w")
        for link in unprocessed_links:
            print "Got a link to download:", link.full_url
            downloaded = link.download()
            links = extract_next_links(downloaded)
            count = 0
            for l in links:
                if is_valid(l):
                    count += 1
                    analyze_link(l)
                    self.frame.add(Adityan1MonishppSkanade1Link(l))
            if count > highest_count:
                highest_count = count
                highest_count_link = link.full_url

        f.write('************** Highest No. of Out Links **************\n')
        f.write('Link with highest count is: '+str(highest_count_link)+'\n')
        f.write('Highest Count = '+str(highest_count)+'\n')
        f.write(
            '************** Subdomains and number of URLs crawled in each one **************\n')
        for key in subdomain_map.keys():
            f.write(str(key)+' = '+str(subdomain_map[key])+'\n')
        f.close()

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

    global largest_link
    global largest_number_of_links

    if rawDataObj.content:
        html_content = lxml.html.fromstring(rawDataObj.content)
        number_of_links = 0
        for link in html_content.iterlinks():
            URL = link[2]
            URLs = re.findall(r'([^:]*?[^:\/]*?\.[^:\/]*?(?:\/|$))', URL)

            if len(URLs) > 1:
                if URLs[0][:2] == '//':
                    URLs[0] = URLs[0][2:]
                URLs = [URLs[0] + ('/' if URLs[0][-1] !=
                                   '/' else '') + p for p in URLs[1:]]
            else:
                URLs = [URL]

            for relative_URL in URLs:
                absolute_URL = relative_URL

                if not urlparse(absolute_URL).netloc:

                    if rawDataObj.is_redirected:
                        host_name = rawDataObj.final_url

                    else:
                        host_name = rawDataObj.url

                    absolute_URL = urljoin(host_name, absolute_URL)

                outputLinks.append(absolute_URL)
                number_of_links += 1

        if number_of_links > largest_number_of_links:
            largest_link = host_name
            largest_number_of_links = number_of_links

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


prev_encountered = set()


def is_valid(url):
    '''
    Function returns True or False based on whether the url has to be
    downloaded or not.
    Robot rules and duplication rules are checked separately.
    This is a great place to filter out crawler traps.
    '''
    url = url.lower()

    if '#' in url:        
        url = url[10:url.rfind('#')]

    if 'mailto' in url:
        return False  # we can easily ignore mail urls

    global prev_encountered
    if url in prev_encountered:
        return False
    prev_encountered.add(url)

    parsed = urlparse(url)

    
    complete_path = parsed.path + parsed.query + parsed.params
    if re.search(r'https?://', complete_path):
        return False

    
    iterations = re.finditer(r'(.+?)\1+', complete_path)
    for iteration in iterations:        
        if len(iteration.group(1)) >= 5:
            return False
    
    max_param_limit = 3
    if len(parse_qs(parsed.query)) >= max_param_limit:
        return False

    if parsed.scheme not in set(["http", "https"]):
        return False

    try:
        return ".ics.uci.edu" in parsed.hostname \
            and not re.match(".*\.(css|js|bmp|gif|jpe?g|ico" + "|png|tiff?|mid|mp2|mp3|mp4"
                             + "|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
                             + "|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso|epub|dll|cnf|tgz|sha1"
                             + "|thmx|mso|arff|rtf|jar|csv"
                             + "|rm|smil|wmv|swf|wma|zip|rar|gz"
                             + "|lif)$", parsed.path.lower())
    except TypeError:
        print ("TypeError for ", parsed)
