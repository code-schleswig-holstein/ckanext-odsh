import datetime,json
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.lib.plugins import DefaultTranslation
from ckan.lib.plugins import DefaultDatasetForm
from ckan.common import OrderedDict
import ckan.lib.helpers as helpers

_ = toolkit._

def odsh_main_groups():
    '''Return a list of the groups to be shown on the start page.'''

    # Get a list of all the site's groups from CKAN, sorted by number of
    # datasets.
    groups = toolkit.get_action('group_list')(
        data_dict={'all_fields': True})

    return groups

def odsh_convert_groups_string(value,context):
    if not value:
        return []
    if type(value) is not list:
        value=[value]
    groups=helpers.groups_available()
    ret = []
    for v in value:
        for g in groups:
            if g['id']==v:
                ret.append(g)
    return ret

     
def odsh_now():
    return helpers.render_datetime(datetime.datetime.now(),"%Y-%m-%d")

def odsh_group_id_selected(selected, group_id):
    if type(selected) is not list:
        selected=[selected]
    for g in selected:
        if (isinstance(g, basestring) and group_id == g) or (type(g) is dict and group_id == g['id']):
            return True

    return False


class OdshPlugin(plugins.SingletonPlugin, DefaultTranslation, DefaultDatasetForm):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IFacets)
    plugins.implements(plugins.IDatasetForm)
    plugins.implements(plugins.IValidators)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'odsh')
    
    def get_helpers(self):
        # Template helper function names should begin with the name of the
        # extension they belong to, to avoid clashing with functions from
        # other extensions.
        return {'odsh_main_groups': odsh_main_groups,
        'odsh_now':odsh_now,
        'odsh_group_id_selected':odsh_group_id_selected}

    def before_map(self, map):
        map.connect('info_page', '/info_page', controller='ckanext.odsh.controller:OdshRouteController', action='info_page')
        return map

    def dataset_facets(self, facets_dict, package_type):
        return OrderedDict({'groups': _('Groups')})

    def organization_facets(self, facets_dict, organization_type, package_type):
        return facets_dict

    def group_facets(self, facets_dict, group_type, package_type):
        return facets_dict

    def _fields(self):
        return ['title','notes']

    def _extraFields(self):
        return ['publish_date','access_constraints','temporal_start','temporal_end','spatial_extension']

    def _update_schema(self,schema):
        for field in self._extraFields():
            schema.update({ field: [
                # toolkit.get_converter('not_empty'),
                toolkit.get_converter('convert_to_extras')] })
        for field in self._fields():
            schema.update({ field: [toolkit.get_converter('not_empty')] })
        # schema.update({ 'groups': [
        #         # toolkit.get_converter('not_empty'),
        #         toolkit.get_converter('odsh_convert_groups_string')] })
        schema['resources'].update({
                'url' : [ toolkit.get_converter('not_empty') ]
                })

    def create_package_schema(self):
        schema = super(OdshPlugin, self).create_package_schema()
        self._update_schema(schema)
        return schema

    def update_package_schema(self):
        schema = super(OdshPlugin, self).update_package_schema()
        self._update_schema(schema)
        return schema

    def show_package_schema(self):
        schema = super(OdshPlugin, self).show_package_schema()
        for field in self._extraFields():
            schema.update({
                field : [toolkit.get_converter('convert_from_extras')]
            })
        return schema

    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return True

    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []

    def get_validators(self): 
        return { 'odsh_convert_groups_string': odsh_convert_groups_string}
    
