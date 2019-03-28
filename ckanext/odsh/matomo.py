from piwikapi.tracking import PiwikTracker
from piwikapi.tests.request import FakeRequest
from ckan.common import c, request
from pylons import config

# def get_request_url_with_params():
#     if request.GET:

def create_matomo_request(userId=None):

    # print(request.url)

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
    piwiktracker = PiwikTracker('1', fakerequest)
    piwiktracker.set_api_url('http://192.168.178.45/piwik.php')
    if userId:
        piwiktracker.set_visitor_id(userId)
    # piwiktracker.set_ip(headers['REMOTE_ADDR']) # Optional, to override the IP
    # piwiktracker.set_token_auth(PIWIK_TOKEN_AUTH)  # Optional, to override the IP
    # print(piwiktracker.do_track_page_view('My Page Title'))
    # print(c.environ['PATH_INFO'])
    piwiktracker.do_track_page_view(request.path_qs)