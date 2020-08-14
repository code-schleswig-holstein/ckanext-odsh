import os
import tempfile
import magic
from pdf2image import convert_from_bytes
import logging
from ckan.common import config 
import urllib2
import requests

from binascii import b2a_hex
import ckan.plugins.toolkit as toolkit
import ckan.logic as logic
#from extension
#from ckanext.odsh.lib.uploader import raise_validation_error_if_virus_found

log = logging.getLogger(__name__)


def create_thumbnail(context, resource):
    '''
    main entry point into this module
    this function is called from pdf_to_thumbnail.plugin
    '''
    old_filename = _get_filename_from_context(context)
    url_type = resource.get('url_type')
    if url_type == 'upload':
        is_PDF, filename = _create_thumbnail_from_memory(resource, old_filename)
    else:
        is_PDF, filename = (False, None)
    return is_PDF, filename  


def _get_filename_from_context(context):
    package = context.get('package')
    package_id = package.id
    package= toolkit.get_action('package_show')(None, {'id': package_id})
    thumbnail = package.get('thumbnail') 
    return  thumbnail


def _create_thumbnail_from_memory(resource, old_filename):
    filepath = get_resource_path(resource)
    is_PDF = _is_pdf(filepath)
    if is_PDF:
        with open(filepath, 'rb') as file:
            new_filename = _create_thumbnail_from_file(file)
        if old_filename:
            ThumbnailPath.from_filename(old_filename).remove()
        return is_PDF, new_filename
    else:
        return is_PDF, None


def get_resource_path(resource):
    # see https://stackoverflow.com/questions/46572402/where-does-ckan-store-the-files-pushed-to-datastore-filestore
    resource_id = resource.get('id')
    filepath = os.path.join(
        config.get('ckan.storage_path'),
        'resources',
        resource_id[0:3],
        resource_id[3:6],
        resource_id[6:]
    )
    return filepath


def _is_pdf(filepath):
    file_type = magic.from_file(filepath, mime = True)
    return file_type == 'application/pdf'


def _create_thumbnail_from_file(file):
    width = config.get('ckan.thumbnail.size.width', 410)
    new_thumbnail = ThumbnailPath.from_unique_random_name()
    file.seek(0)
    file_read = file.read()
    convert_from_bytes(
        file_read,
        size=(width, None),
        output_folder=new_thumbnail.folder,
        output_file=new_thumbnail.filename,
        single_file=True,
        first_page=0,
        last_page=0,
        fmt='jpg'
    )
    return new_thumbnail.filename_with_extension


def thumbnail_folder():
    return os.path.join(
        config.get('ckan.storage_path'),
        'thumbnail',
    )


def rename_thumbnail_to_random_name(old_filename):
    '''
    used by pdf_to_thumbnail.action
    '''
    old_filepath = ThumbnailPath.from_filename_with_extension(old_filename)
    new_filepath = ThumbnailPath.from_unique_random_name()
    try:
        os.renames(old_filepath.full_filename, new_filepath.full_filename)
        return new_filepath.filename_with_extension
    except OSError:
        log.warning('The file path "{}"  of package was not found.'.format(old_filepath))
     

def remove_thumbnail(context):
    '''
    used by pdf_to_thumbnail.action
    '''
    old_filename = _get_filename_from_context(context)
    if old_filename:
        ThumbnailPath.from_filename_with_extension(old_filename).remove()


def resources_of_containing_package(resource):
    #todo: change arg order
    '''
    used by pdf_to_thumbnail.plugin
    '''
    package_id = resource.get('package_id')
    package = toolkit.get_action('package_show')(None, {'id': package_id})
    resources = package.get('resources')
    return resources
        

def create_thumbnail_if_none_in_package(context, resources):
    '''
    used by pdf_to_thumbnail.plugin
    loops through a package's resources in the order they have been uploaded
    and for each tries to create a thumbnail until it succeeds.
    If the package already has a thumbnail the creation step is skipped
    '''
    package_dict = _get_package_dict_from_context(context)
    if not _has_thumbnail(package_dict):
        any(_try_create_thumbnail(context, r) for r in resources)


def _get_package_dict_from_context(context):
    package_id = context.get('package').id
    package_dict = toolkit.get_action('package_show')(None, {'id': package_id})
    return package_dict


def _has_thumbnail(package_dict):
    thumbnail = package_dict.get('thumbnail')
    return bool(thumbnail)


def _try_create_thumbnail(context, resource):
    is_PDF, filename = create_thumbnail(context, resource)
    success = is_PDF
    if success:
        _write_thumbnail_into_package(context, filename)
    return success


def _write_thumbnail_into_package(context, filename):
    package_dict = _get_package_dict_from_context(context)
    if filename:
        package_dict.update({'thumbnail': filename})
    toolkit.get_action('package_update')(None, package_dict)
    

class ThumbnailPath(object):
    '''
    utility class to manage the path of thumbnail pictures
    '''

    def __init__(self, folder, filename, extension):
        self.folder = folder
        self.filename = filename
        self.extension = extension
    
    _EXTENSION = '.jpg'
    
    @staticmethod
    def from_filename(filename):
        '''
        filename without extension (i.e. '.jpg')
        '''
        return ThumbnailPath(thumbnail_folder(), filename, ThumbnailPath._EXTENSION)
    
    @staticmethod
    def from_filename_with_extension(filename_with_extension):
        '''
        limited to one dot in filename
        '''
        tokens = filename_with_extension.split('.')
        if len(tokens) == 1:
            filename = filename_with_extension
            extension = ''
        else:
            filename = '.'.join(tokens[:-1])
            extension = '.'.join(['', tokens[-1]])
        return ThumbnailPath(thumbnail_folder(), filename, extension)

    @staticmethod
    def from_unique_random_name():
        thumbnail_path = ThumbnailPath._from_random_name()
        if thumbnail_path.exists():
            return ThumbnailPath.from_unique_random_name()
        return thumbnail_path
    
    @staticmethod
    def _from_random_name():
        number = b2a_hex(os.urandom(15))
        filename = 'thumbnail_picture_' + str(number)
        return ThumbnailPath.from_filename(filename)
    
    @property
    def filename_with_extension(self):
        return self.filename + self.extension
    
    @property
    def full_filename(self):
        return os.path.join(self.folder, self.filename_with_extension)
    
    def exists(self):
        return os.path.exists(self.full_filename)
    
    def remove(self):
        if os.path.exists(self.full_filename):
            os.remove(self.full_filename)
