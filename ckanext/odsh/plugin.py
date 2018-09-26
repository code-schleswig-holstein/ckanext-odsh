import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.lib.plugins import DefaultTranslation
from ckan.common import OrderedDict

_ = toolkit._

def odsh_main_groups():
    '''Return a list of the groups to be shown on the start page.'''

    # Get a list of all the site's groups from CKAN, sorted by number of
    # datasets.
    groups = toolkit.get_action('group_list')(
        data_dict={'all_fields': True})

    return groups

class OdshPlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IFacets)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'odsh')
    
    def get_helpers(self):
        # Template helper function names should begin with the name of the
        # extension they belong to, to avoid clashing with functions from
        # other extensions.
        return {'odsh_main_groups': odsh_main_groups}

    def before_map(self, map):
        map.connect('info_page', '/info_page', controller='ckanext.odsh.controller:OdshRouteController', action='info_page')
        return map

    def dataset_facets(self, facets_dict, package_type):
        return OrderedDict({'groups': _('Groups')})

    def group_facets(self, facets_dict, group_type, package_type):
        return facets_dict