'''
Created on Oct 20, 2016
@author: Rohan Achar
'''
from rtypes.pcc.attributes import dimension, primarykey, predicate
from rtypes.pcc.types.subset import subset
from rtypes.pcc.types.set import pcc_set
from rtypes.pcc.types.projection import projection
from rtypes.pcc.types.impure import impure
from datamodel.search.server_datamodel import Link, ServerCopy

@pcc_set
class Adityan1MonishppSkanade1Link(Link):
    USERAGENTSTRING = "Adityan1MonishppSkanade1"

    @dimension(str)
    def user_agent_string(self):
        return self.USERAGENTSTRING

    @user_agent_string.setter
    def user_agent_string(self, v):
        # TODO (rachar): Make it such that some dimensions do not need setters.
        pass


@subset(Adityan1MonishppSkanade1Link)
class Adityan1MonishppSkanade1UnprocessedLink(object):
    @predicate(Adityan1MonishppSkanade1Link.download_complete, Adityan1MonishppSkanade1Link.error_reason)
    def __predicate__(download_complete, error_reason):
        return not (download_complete or error_reason)


@impure
@subset(Adityan1MonishppSkanade1UnprocessedLink)
class OneAdityan1MonishppSkanade1UnProcessedLink(Adityan1MonishppSkanade1Link):
    __limit__ = 1

    @predicate(Adityan1MonishppSkanade1Link.download_complete, Adityan1MonishppSkanade1Link.error_reason)
    def __predicate__(download_complete, error_reason):
        return not (download_complete or error_reason)

@projection(Adityan1MonishppSkanade1Link, Adityan1MonishppSkanade1Link.url, Adityan1MonishppSkanade1Link.download_complete)
class Adityan1MonishppSkanade1ProjectionLink(object):
    pass
