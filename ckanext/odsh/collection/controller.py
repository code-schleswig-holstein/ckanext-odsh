from ckan.lib.helpers import is_url, url_for
import ckan.plugins.toolkit as toolkit
from ckan.controllers.package import PackageController
from helpers import get_latest_resources_for_type, get_latest_dataset



class LatestDatasetController(PackageController):
    
    def latest_dataset(self, id):
        latest_dataset= get_latest_dataset(id)
        toolkit.redirect_to(controller='package', action='read', id=latest_dataset)

class LatestRecourcesController(PackageController):
    
    def latest_resource(self, id, type):
        latest_resources = get_latest_resources_for_type(id, type)
        if latest_resources is None:
            abort(404)
        url_type = latest_resources.get('url_type')
        if url_type is None:
            resource_url = latest_resources.get('url')
            toolkit.redirect_to(resource_url)
        if url_type == 'upload':
            download_package_id = latest_resources.get('package_id')
            download_resource_id = latest_resources.get('id')
            pre_resource_url = latest_resources.get('url')
            if is_url(pre_resource_url):
                url_resource = pre_resource_url
            else:
                url_resource = url_for(controller='package',
                                    action='resource_download',
                                    id=download_package_id,
                                    resource_id=download_resource_id,
                                    filename=pre_resource_url,
                                    qualified = True)
            toolkit.redirect_to(url_resource)
        abort(404)