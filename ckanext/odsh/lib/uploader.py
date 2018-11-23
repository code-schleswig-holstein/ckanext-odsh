import ckan.logic as logic
from ckan.lib.uploader import ResourceUpload
from odsh_icap_client import ODSHICAPRequest

import logging

log = logging.getLogger(__name__)

ValidationError = logic.ValidationError

class ODSHResourceUpload(ResourceUpload):

    def __init__(self, resource):
        super(ODSHResourceUpload, self).__init__(resource)
        if self._icap_virus_found():
            raise ValidationError(['Virus gefunden'])
        
    def _icap_virus_found(self):
        response_object = ODSHICAPRequest(self.filename, self.upload_file).send()
        return response_object.virus_found()
        
