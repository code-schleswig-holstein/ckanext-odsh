import ckan.plugins as plugins
from ckanext.odsh.lib.uploader import ODSHResourceUpload, ODSHUpload

class OdshIcapPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IUploader, inherit=True)

    def get_resource_uploader(self, data_dict):
        return ODSHResourceUpload(data_dict)
    
    def get_uploader(self, upload_to, old_filename):
        return ODSHUpload(upload_to, old_filename)