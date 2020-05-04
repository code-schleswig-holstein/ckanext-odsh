import os
import tempfile
import magic
from pdf2image import convert_from_bytes
import logging
from ckan.common import config 
import urllib2
import requests

import binascii
import ckan.plugins.toolkit as toolkit
import ckan.logic as logic
#from extension
#from ckanext.odsh.lib.uploader import raise_validation_error_if_virus_found

log = logging.getLogger(__name__)
 

def get_filename_from_context(context):
    package = context.get('package')
    package_id = package.id
    package= toolkit.get_action('package_show')(context, {'id': package_id})
    thumbnail = package.get('thumbnail') 
    return  thumbnail

def get_filepath_for_thumbnail(filename):
    if filename:
        return config.get('ckan.storage_path') + "/thumbnail/" + filename
    return config.get('ckan.storage_path') + "/thumbnail/"

def concatenate_filename(filename):
    return filename + ".jpg"

def get_filepath_to_resource(resource):
    resource_id = resource.get('id')
    directory = config.get('ckan.storage_path') + '/resources/'
    #looked up how resources are saved, by locating the keyword resources in the OS 
    path = directory + resource_id[0:3] + '/' + resource_id[3:6] + '/' +  resource_id[6:]
    return path

def random_filename():
    number = binascii.b2a_hex(os.urandom(15))
    filename = 'thumbnail_picture_' + str(number)    
    full_filename = concatenate_filename(filename)
    filepath = get_filepath_for_thumbnail(full_filename)
    if os.path.exists(filepath):
        filename = random_filename()
    return filename

def change_filepath(old_filename):    
    old_filepath = get_filepath_for_thumbnail(old_filename)
    new_filename = concatenate_filename(random_filename())
    new_filepath = get_filepath_for_thumbnail(new_filename)
    try:
        os.renames(old_filepath, new_filepath)
        return new_filename
    except OSError:
        log.warning('The file path "{}"  of package was not found.'.format(old_filepath))
     

def create_thumbnail_from_file(file, old_filename):
    width = config.get('ckan.thumbnail.size.width', 410)
    filename = random_filename()
    file.seek(0)
    file_read = file.read()
    directory = get_filepath_for_thumbnail('')
    if old_filename:
        old_filepath = get_filepath_for_thumbnail(concatenate_filename(old_filename))
        if os.path.exists(old_filepath):
            os.remove(old_filepath)
    convert_from_bytes(file_read,
                       size=(width, None),
                       output_folder=directory,
                       output_file=filename,
                       single_file=True,
                       first_page=0,
                       last_page=0,
                       fmt='jpg'
                       )
    return concatenate_filename(filename)


def create_thumbnail_from_url(resource, old_filename):
    resource_url = resource.get('url')
    request = urllib2.Request(resource_url)
    response = urllib2.urlopen(request, timeout = 100000) 
    
    
    if response.code == 200:
        filetowrite = response.read()
        # function is set to private in ckanext.odsh.lib.uploader
        # raise_validation_error_if_virus_found(filetowrite, response.read())
        file_type = magic.from_buffer(response.read(), mime = True)
        header = response.headers
        resource_size = header.get('Content-Length')
        
            
        max_available_memory = config.get('ckan.max_available_memory', 250000000)  #In Bytes ca. 250 MB
        with tempfile.SpooledTemporaryFile(max_size=max_available_memory) as file:
            file.write(filetowrite)
            
            new_filename = create_thumbnail_from_file(file, old_filename)        
            return True, new_filename

def create_thumbnail_from_memory(resource, old_filename):
    path = get_filepath_to_resource(resource)
    file_type = magic.from_file(path, mime = True)
    if file_type == 'application/pdf':
        with open(path, 'rb') as file:
            new_filename = create_thumbnail_from_file(file, old_filename)
        is_PDF = True
        return is_PDF, new_filename
    else:
        is_PDF = False
        return is_PDF,  None

def remove_thumbnail(context):
    old_filename = get_filename_from_context(context)
    if old_filename:
        old_filepath = get_filepath_for_thumbnail(old_filename)
        if os.path.exists(old_filepath):
            os.remove(old_filepath)

def create_thumbnail(context, resource):
    log.debug('create_thumbnail')
    old_filename = get_filename_from_context(context)
    url_type = resource.get('url_type')
    if url_type == 'upload':
        is_PDF,  filename = create_thumbnail_from_memory(resource, old_filename)
    else:
        is_PDF,  filename = create_thumbnail_from_url(resource, old_filename)
    return is_PDF,  filename   

def check_and_create_thumbnail_after_update(context, resource):
    log.debug('check_and_create_thumbnail_after_update')
    package_id = resource.get('package_id')
    package = toolkit.get_action('package_show')(context, {'id': package_id})
    resources = package.get('resources')
    if len(resources) > 0:
        last_resource = resources.pop()
        last_resource_id = last_resource.get('id')
        resource_id = resource.get('id')
    if last_resource_id == resource_id and resource.get('url_type') != 'upload':
        is_PDF,  filename = create_thumbnail(context, resource)
        if is_PDF:
            write_thumbnail_into_package(context, resource, filename)  
        

def create_thumbnail_for_last_resource(context, resources):
    if len(resources) > 0:
        last_resource = resources.pop()
        is_PDF, filename = create_thumbnail(context, last_resource)
        if not is_PDF:
            create_thumbnail_for_last_resource(context, resources)
        else:
            write_thumbnail_into_package(context, last_resource, filename)
    else:
        remove_thumbnail(context)
        package = context.get('package')
        package_id = package.id
        package= toolkit.get_action('package_show')(context, {'id': package_id})
        package.update({'thumbnail': None})
        toolkit.get_action('package_update')(context, package)

def write_thumbnail_into_package(context, resource, filename):
        package_id = resource.get('package_id')
        package = toolkit.get_action('package_show')(context, {'id': package_id})
        if filename:
            package.update({'thumbnail': filename})
        toolkit.get_action('package_update')(context, package)
