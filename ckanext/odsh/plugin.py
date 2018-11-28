import datetime,json
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.lib.plugins import DefaultTranslation
from ckan.lib.plugins import DefaultDatasetForm
from ckan.common import OrderedDict
from ckanext.odsh.lib.uploader import ODSHResourceUpload
import ckan.lib.helpers as helpers
import helpers as odsh_helpers
from routes.mapper import SubMapper
from pylons import config
import urllib2
import csv

import logging

log = logging.getLogger(__name__)

_ = toolkit._

def odsh_get_facet_items_dict(name, limit=None):
    ''' 
    Gets all facets like 'get_facet_items_dict' but sorted alphabetically
    instead by count.
    '''
    facets = helpers.get_facet_items_dict(name, limit)
    facets.sort(key=lambda it: (it['display_name'].lower(), -it['count']))
    log.info(facets)
    return facets

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


def known_spatial_uri(key, data, errors, context):
    mapping_file = config.get('ckanext.odsh.spatial.mapping')
    try:
        mapping_file = urllib2.urlopen(mapping_file)
    except Exception:
        raise Exception("Could not load spatial mapping file!")

    not_found = True
    spatial_text = str()
    spatial = str()
    cr = csv.reader(mapping_file, delimiter="\t")
    for row in cr:
        if row[0] == data[key]:
            not_found = False
            spatial_text = row[1]
            loaded = json.loads(row[2])
            spatial = json.dumps(loaded['geometry'])
            print spatial
            break
    if not_found:
        raise toolkit.Invalid("The specified URI is not known")

    # Get the current extras index
    current_indexes = [k[1] for k in data.keys()
                       if len(k) > 1 and k[0] == 'extras']

    new_index = max(current_indexes) + 1 if current_indexes else 0

    data[('extras', new_index, 'key')] = 'spatial_text'
    data[('extras', new_index, 'value')] = spatial_text
    data[('extras', new_index+1, 'key')] = 'spatial'
    data[('extras', new_index+1, 'value')] = spatial


class OdshIcapPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IUploader, inherit=True)

    def get_resource_uploader(self, data_dict):
        return ODSHResourceUpload(data_dict)


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
                'odsh_now': odsh_now,
                'odsh_group_id_selected': odsh_group_id_selected,
                'odsh_get_facet_items_dict': odsh_get_facet_items_dict,
                'odsh_openness_score_dataset_html': odsh_helpers.odsh_openness_score_dataset_html,
                'odsh_get_resource_details': odsh_helpers.odsh_get_resource_details,
                'odsh_get_resource_views': odsh_helpers.odsh_get_resource_views
        }

    def before_map(self, map):
        map.connect('info_page', '/info_page', controller='ckanext.odsh.controller:OdshRouteController', action='info_page')

        # redirect all user routes to custom controller
        with SubMapper(map, controller='ckanext.odsh.controller:OdshUserController') as m:
            m.connect('/user/edit', action='edit')
            m.connect('user_generate_apikey', '/user/generate_key/{id}', action='generate_apikey')
            m.connect('/user/activity/{id}/{offset}', action='activity')
            m.connect('user_activity_stream', '/user/activity/{id}',
                    action='activity', ckan_icon='clock-o')
            m.connect('user_dashboard', '/dashboard', action='dashboard',
                    ckan_icon='list')
            m.connect('user_dashboard_datasets', '/dashboard/datasets',
                    action='dashboard_datasets', ckan_icon='sitemap')
            m.connect('user_dashboard_groups', '/dashboard/groups',
                    action='dashboard_groups', ckan_icon='users')
            m.connect('user_dashboard_organizations', '/dashboard/organizations',
                    action='dashboard_organizations', ckan_icon='building-o')
            m.connect('/dashboard/{offset}', action='dashboard')
            m.connect('user_follow', '/user/follow/{id}', action='follow')
            m.connect('/user/unfollow/{id}', action='unfollow')
            m.connect('user_followers', '/user/followers/{id:.*}',
                    action='followers', ckan_icon='users')
            m.connect('user_edit', '/user/edit/{id:.*}', action='edit',
                    ckan_icon='cog')
            m.connect('user_delete', '/user/delete/{id}', action='delete')
            m.connect('/user/reset/{id:.*}', action='perform_reset')
            m.connect('register', '/user/register', action='register')
            m.connect('login', '/user/login', action='login')
            m.connect('/user/_logout', action='logout')
            m.connect('/user/logged_in', action='logged_in')
            m.connect('/user/logged_out', action='logged_out')
            m.connect('/user/logged_out_redirect', action='logged_out_page')
            m.connect('/user/reset', action='request_reset')
            m.connect('/user/me', action='me')
            m.connect('/user/set_lang/{lang}', action='set_lang')
            m.connect('user_datasets', '/user/{id:.*}', action='read',
                    ckan_icon='sitemap')
            m.connect('user_index', '/user', action='index')
        
        return map

    def dataset_facets(self, facets_dict, package_type):
        # TODO: Frage von Pascal 12.10.2018: warum ist die Ordnung hier genau umgekehrt (von hinten nach vorne?)
        # Christian: ist sie wohl nicht, ckan sortiert das einfach irgendwie neu
        return OrderedDict({'organization': _('Herausgeber'),
                            'res_format': _('Dateiformat'),
                            'license_title': _('Lizenz'),
                           'groups': _('Kategorie')})

    def organization_facets(self, facets_dict, organization_type, package_type):
        return OrderedDict({'organization': _('Herausgeber'),
                            'res_format': _('Dateiformat'),
                            'license_title': _('Lizenz'),
                           'groups': _('Kategorie')})

    def group_facets(self, facets_dict, group_type, package_type):
        return OrderedDict({'organization': _('Herausgeber'),
                            'res_format': _('Dateiformat'),
                            'license_title': _('Lizenz'),
                           'groups': _('Kategorie')})

    def _fields(self):
        # return ['title','notes','tag_string']
        return ['title','notes']

    def _extraFields(self):
        ##return ['publish_date','access_constraints','temporal_start','temporal_end','spatial_uri']
        return ['publish_date', 'temporal_start', 'temporal_end', 'spatial_uri']
        ##return ['publish_date','access_constraints','temporal_start','temporal_end','spatial_extension']
        return ['publish_date','temporal_start','temporal_end','spatial_extension']
    def _extraFieldsOptional(self):
        return ['access_constraints']

    def _update_schema(self,schema):
        for field in self._extraFields():
            if field == 'spatial_uri':
                schema.update({field: [
                    toolkit.get_converter('not_empty'),
                    toolkit.get_validator('ignore_missing'),
                    toolkit.get_converter('known_spatial_uri'),
                    toolkit.get_converter('convert_to_extras')]})
            else:
                schema.update({field: [
                    toolkit.get_converter('not_empty'),
                    toolkit.get_validator('ignore_missing'),
                    toolkit.get_converter('convert_to_extras')]})
        for field in self._fields():
            schema.update({field: [toolkit.get_converter('not_empty')]})
        # schema.update({ 'groups': [
        #         # toolkit.get_converter('not_empty'),
        #         toolkit.get_converter('odsh_convert_groups_string')] })
        schema['resources'].update({
                'url' : [ toolkit.get_converter('not_empty') ]
                # 'description' : [ toolkit.get_converter('not_empty') ],
                # 'name' : [ toolkit.get_converter('not_empty') ]
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
        for field in self._extraFields()+self._extraFieldsOptional():
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
        return { 'odsh_convert_groups_string': odsh_convert_groups_string,
                 'known_spatial_uri': known_spatial_uri}
    
