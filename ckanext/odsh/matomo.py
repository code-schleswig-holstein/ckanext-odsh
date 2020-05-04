from piwikapi.tracking import PiwikTracker
from piwikapi.tests.request import FakeRequest
from ckan.common import c, request
from pylons import config
import logging
from ckan.plugins.toolkit import enqueue_job
import ckanext.odsh.helpers_tpsh as helpers_tpsh

def do_if_use_matomo(func):
    def wrapper(*args, **kwargs):
        use_matomo = helpers_tpsh.use_matomo()
        if use_matomo:
            return func(*args, **kwargs)
    return wrapper

@do_if_use_matomo
def create_matomo_request(userId=None):
    headers = {
        'HTTP_USER_AGENT': request.headers.get('User-Agent'),
        'REMOTE_ADDR': request.headers.get('Host'),
        # 'HTTP_REFERER': 'http://referer.com/somewhere/',
        'HTTP_ACCEPT_LANGUAGE': request.headers.get('Accept-Language'),
        'SERVER_NAME': config.get('ckan.site_url'),
        'PATH_INFO': c.environ['PATH_INFO'],
        # 'QUERY_STRING': 'something=bar',
        'HTTPS': False,
    }
    fakerequest = FakeRequest(headers)
    piwiktracker =PiwikTracker(config.get('ckanext.odsh.matomo_id'), fakerequest)
    piwiktracker.set_api_url(config.get('ckanext.odsh.matomo_url'))
    if userId:
        piwiktracker.set_visitor_id(userId)
    enqueue_job(piwiktracker.do_track_page_view,[request.path_qs], queue='tracking')
