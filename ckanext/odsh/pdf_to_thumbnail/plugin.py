import os 


#from ckan
import ckan.plugins as plugins

#pdf_to_thumbnail 
import thumbnail 
import action as thumbnail_action
import helpers as thumbnail_helpers

import logging
log = logging.getLogger(__name__)


class ThumbnailPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IResourceController, inherit=True)
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IActions, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)


#IResourceController
    def after_create(self, context, resource):        
        _, filename = thumbnail.create_thumbnail(context, resource)
        thumbnail.write_thumbnail_into_package(context, resource, filename)
        
    def after_update(self, context, resource):
        thumbnail.check_and_create_thumbnail_after_update(context, resource)
                
    def after_delete(self, context, resources):
        thumbnail.create_thumbnail_for_last_resource(context, resources)
            
#IConfigurer 

    def update_config(self, config_):
        storage_path = config_.get('ckan.storage_path')
        public_dir = os.path.join(storage_path, 'thumbnail')
        if config_.get('extra_public_paths'):
            config_['extra_public_paths'] += ',' + public_dir
        else:
            config_['extra_public_paths'] = public_dir

#IActions

    def get_actions(self):
        return {'package_delete': thumbnail_action.before_package_delete,
                'package_update': thumbnail_action.before_package_update 
                }

#ITemplateHelpers

    def get_helpers(self):
        
        return {
                'thumbnail_namespace':thumbnail_helpers.thumbnail_namespace,
                'thumbail_get_download_link':thumbnail_helpers.get_download_link_for_thumbnail
                }
