import urllib2
from ckan.common import config


def setup_proxy():
    '''
    This function declares that a proxy server shall be used to access the web via
    urllib2. It takes the proxy address from ckan's config file 
    (
        field "ckanext.odsh.download_proxy",
        example: ckanext.odsh.download_proxy = http://1.2.3.4:4123
    )
    '''

    proxy_url = config.get('ckanext.odsh.download_proxy', None)
    if proxy_url:
        proxy = urllib2.ProxyHandler({'http': proxy_url, 'https': proxy_url})
        opener = urllib2.build_opener(proxy)
        urllib2.install_opener(opener)

def clear_proxy():
    proxy = urllib2.ProxyHandler({})
    opener = urllib2.build_opener(proxy)
    urllib2.install_opener(opener)