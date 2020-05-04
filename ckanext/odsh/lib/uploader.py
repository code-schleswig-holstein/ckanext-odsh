import ckan.logic as logic
from ckan.lib.uploader import ResourceUpload, Upload
import ckan.plugins.toolkit as toolkit
from pylons import config

from odsh_icap_client import ODSHICAPRequest
import logging
import hashlib

log = logging.getLogger(__name__)


def _icap_virus_found(filename, upload_file):
    # the flag skip_icap_virus_check in can be used during development
    skip_icap_virus_check = toolkit.asbool(
        config.get('ckanext.odsh.skip_icap_virus_check', 'False')
    )
    if skip_icap_virus_check:
        log.debug("WARNING: icap virus check skipped, remove parameter ckanext.odsh.skip_icap_virus_check from ckan's ini file")
        return False
    if filename and upload_file:
        response_object = ODSHICAPRequest(filename, upload_file).send()
        return response_object.virus_found()


def _raise_validation_error_if_virus_found(filename, upload_file):
    if _icap_virus_found(filename, upload_file):
        raise logic.ValidationError({'upload': ['Virus gefunden']})


def calculate_hash(upload_file):
    upload_file.seek(0)
    hash_md5 = hashlib.md5()
    for chunk in iter(lambda: upload_file.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()
    #return hashlib.md5(upload_file.read()).hexdigest() 


def _raise_validation_error_if_hash_values_differ(upload_file, resource):
    hash_from_resource = resource.get('hash') 
    if hash_from_resource:
        hash_from_calculation = calculate_hash(upload_file)
        if not hash_from_calculation == hash_from_resource:
            log.debug('hash from calculation: {}'.format(hash_from_calculation))
            log.debug('hash from resource: {}'.format(hash_from_resource))
            raise logic.ValidationError({'upload': ['Berechneter Hash und mitgelieferter Hash sind unterschiedlich']})
            

class ODSHResourceUpload(ResourceUpload):

    def __init__(self, resource):
        log.debug("Resource({}) uploaded.".format(resource))
        super(ODSHResourceUpload, self).__init__(resource)
        if hasattr(self, 'filename') and hasattr(self, 'upload_file'):
            _raise_validation_error_if_virus_found(self.filename, self.upload_file)
            _raise_validation_error_if_hash_values_differ(self.upload_file, resource)


class ODSHUpload(Upload):
    '''
    custom uploader to upload resources and group images
    see https://docs.ckan.org/en/ckan-2.7.3/extensions/plugin-interfaces.html?highlight=iuploader#ckan.plugins.interfaces.IUploader
    this uploader object hooks into the upload method in order to 
    scan for viruses within the uploaded content
    '''

    def __init__(self, upload_to, old_filename=None):
        super(ODSHUpload, self).__init__(upload_to, old_filename)
    
    def update_data_dict(self, data_dict, url_field, file_field, clear_field):
        super(ODSHUpload, self).update_data_dict(data_dict, url_field, file_field, clear_field)
    
    def upload(self, max_size=2):
        if hasattr(self, 'filename') and hasattr(self, 'upload_file'):
            _raise_validation_error_if_virus_found(self.filename, self.upload_file)
        super(ODSHUpload, self).upload(max_size)