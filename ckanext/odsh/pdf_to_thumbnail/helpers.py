
from ckan.lib.helpers import is_url, url_for

def thumbnail_namespace(filename):
    return "/" + filename

def get_download_link_for_thumbnail(package):
    resources = package.get('resources')
    for resource in resources[::-1]:
        url_type =resource.get('url_type')
        mimetype = resource.get('mimetype')
        if url_type == 'upload' and mimetype == 'application/pdf':
            package_id = resource.get('package_id')
            resource_id = resource.get('id')
            pre_resource_url = resource.get('url')
            if is_url(pre_resource_url):
                url_resource = pre_resource_url
            else:
                url_resource = url_for(controller='package',
                                    action='resource_download',
                                    id=package_id,
                                    resource_id=resource_id,
                                    filename=pre_resource_url,
                                    qualified = True)
            
            
            return url_resource
