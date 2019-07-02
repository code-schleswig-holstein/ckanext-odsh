import ckan.logic as logic
from ckan.lib.uploader import ResourceUpload
from odsh_icap_client import ODSHICAPRequest

#import logging

#log = logging.getLogger(__name__)


class ODSHResourceUpload(ResourceUpload):

    def __init__(self, resource):
        #log.info("Resource({}) uploaded.".format(resource))
        super(ODSHResourceUpload, self).__init__(resource)
        if self._icap_virus_found():
            #log.info("Found Virus!")
            raise logic.ValidationError({'upload': ['Virus gefunden']})
        
    def _icap_virus_found(self):
        if self.filename and self.upload_file:
            response_object = ODSHICAPRequest(self.filename, self.upload_file).send()
            return response_object.virus_found()
        
