# ckan
import ckan.plugins.toolkit as toolkit
import ckan.lib.helpers as helpers
from ckan.logic.action.update import package_update
from ckan.logic.action.delete import package_delete

import thumbnail


def before_package_delete(context, package_id_dict):
    pkg_dict = toolkit.get_action('package_show')(context, package_id_dict)
    if helpers.check_access('package_delete', pkg_dict):
        thumbnail.remove_thumbnail(context)
    return package_delete(context, package_id_dict)
    
def before_package_update(context, pkg_dict):
    if helpers.check_access('package_update', pkg_dict):
        package_id =pkg_dict.get('id') 
        package = toolkit.get_action('package_show')(context, {'id': package_id})
        old_private = package.get('private')
        new_private = pkg_dict.get('private')
        old_filename = package.get('thumbnail')
        if old_filename:
            if str(old_private) != str(new_private):
                new_filename = thumbnail.rename_thumbnail_to_random_name(old_filename)
                pkg_dict['extras'].append({'key': 'thumbnail', 'value': new_filename})
            elif not pkg_dict.get('thumbnail'): 
                pkg_dict['extras'].append({'key': 'thumbnail', 'value': old_filename})
    return package_update(context, pkg_dict)