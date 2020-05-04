import os
from ckanext.odsh.pdf_to_thumbnail.thumbnail import get_filepath_to_resource
from ckanext.odsh.lib.uploader import calculate_hash
import ckan.plugins.toolkit as toolkit
import magic
import pdftotext

def add_attributes_resources(context, resource):
    package_id = resource.get('package_id')
    package = toolkit.get_action('package_show')(context, {'id': package_id})
    resources = package.get('resources')
    i = 0
    for item in resources:    
        if item.get('id') == resource.get('id'):
            path = get_filepath_to_resource(resource)
            if os.path.exists(path):
                with open(path, 'rb') as file:                  
                    
                    #size
                    if not item.get('size'):
                        resource_size = os.path.getsize(path)
                        item.update({'size': resource_size})
                    
                    #hash
                    file.seek(0)
                    hash = calculate_hash(file)
                    item.update({'hash':hash})
                    
                    #hash algorithm
                    item.update({'hash_algorithm': 'http://dcat-ap.de/def/hashAlgorithms/md/5'})
                    
            
                    #number of pages
                    file_type = magic.from_file(path, mime = True)                    
                    if file_type == 'application/pdf':
                        file.seek(0)            
                        pdf = pdftotext.PDF(file)
                        number_of_pages = len(pdf)
                        item.update({'number_of_pages':number_of_pages})

                    resources[i] = item 
            break                         
        i = i + 1  
    package.update({'resources':resources})
    toolkit.get_action('package_update')(context, package)
