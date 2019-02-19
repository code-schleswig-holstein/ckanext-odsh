import datetime
import json
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.lib.plugins import DefaultTranslation
from ckan.lib.plugins import DefaultDatasetForm
from ckan.lib.navl.dictization_functions import Missing
from ckan.logic.validators import tag_string_convert
from ckan.common import OrderedDict
from ckanext.odsh.lib.uploader import ODSHResourceUpload
import ckan.lib.helpers as helpers
import helpers as odsh_helpers

from itertools import count
from routes.mapper import SubMapper
from pylons import config
import urllib2
import csv
import re
from dateutil.parser import parse

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


def odsh_convert_groups_string(value, context):
    if not value:
        return []
    if type(value) is not list:
        value = [value]
    groups = helpers.groups_available()
    ret = []
    for v in value:
        for g in groups:
            if g['id'] == v:
                ret.append(g)
    return ret


def odsh_now():
    return helpers.render_datetime(datetime.datetime.now(), "%Y-%m-%d")


def odsh_group_id_selected(selected, group_id):
    if type(selected) is not list:
        selected = [selected]
    for g in selected:
        if (isinstance(g, basestring) and group_id == g) or (type(g) is dict and group_id == g['id']):
            return True

    return False


def known_spatial_uri(key, data, errors, context):
    value = _extract_value(data, 'spatial_uri')

    if not value:
        raise toolkit.Invalid('spatial_uri:odsh_spatial_uri_error_label')

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
        if row[0].encode('UTF-8') == value:
            not_found = False
            spatial_text = row[1]
            loaded = json.loads(row[2])
            spatial = json.dumps(loaded['geometry'])
            break
    if not_found:
        raise toolkit.Invalid(
            'spatial_uri:odsh_spatial_uri_unknown_error_label')

    # Get the current extras index
    current_indexes = [k[1] for k in data.keys()
                       if len(k) > 1 and k[0] == 'extras']

    new_index = max(current_indexes) + 1 if current_indexes else 0

    data[('extras', new_index, 'key')] = 'spatial_text'
    data[('extras', new_index, 'value')] = spatial_text
    data[('extras', new_index+1, 'key')] = 'spatial'
    data[('extras', new_index+1, 'value')] = spatial


def _extract_value(data, field):
    key = None
    for k in data.keys():
        if data[k] == field:
            key = k
            break
    if key is None:
        return None
    return data[(key[0], key[1], 'value')]

def _set_value(data, field, value):
    key = None
    for k in data.keys():
        if data[k] == field:
            key = k
            break
    if key is None:
        return None
    data[(key[0], key[1], 'value')] = value

def odsh_validate_extra_date(key, field, data, errors, context):
    value = _extract_value(data, field)

    if not value:
        if field == 'temporal_end':
            return # temporal_end is optional
        # Statistikamt Nord does not always provide temporal_start/end,
        # but their datasets have to be accepted as they are.
        if not ('id',) in data or data[('id',)][:7] != 'StaNord':
            raise toolkit.Invalid(field+':odsh_'+field+'_error_label')
    else:
        if re.match(r'\d\d\d\d-\d\d-\d\d', value):
            try:
                dt=parse(value)
                _set_value(data, field, dt.isoformat())
                return
            except ValueError:
                pass
        raise toolkit.Invalid(field+':odsh_'+field+'_not_date_error_label')


def odsh_validate_extra_date_factory(field):
    return lambda key, data, errors, context: odsh_validate_extra_date(key, field, data, errors, context)

def odsh_delete_licenseAttributionByText_if_empty(key, data, errors, context):
    for k in data:
        if data[k] == 'licenseAttributionByText':
            if isinstance(data[(k[0], k[1], 'value')], Missing):
                del data[(k[0], k[1], 'value')]
                del data[(k[0], k[1], 'key')]
                break

def odsh_tag_name_validator(value, context):
    tagname_match = re.compile('[\w \-.\:\(\)]*$', re.UNICODE)
    if not tagname_match.match(value):
        raise toolkit.Invalid(_('Tag "%s" must be alphanumeric '
                                'characters or symbols: -_.:()') % (value))
    return value


def odsh_tag_string_convert(key, data, errors, context):
    '''Takes a list of tags that is a comma-separated string (in data[key])
    and parses tag names. These are added to the data dict, enumerated. They
    are also validated.'''
    if isinstance(data[key], basestring):
        tags = [tag.strip()
                for tag in data[key].split(',')
                if tag.strip()]
    else:
        tags = data[key]

    current_index = max([int(k[1]) for k in data.keys()
                         if len(k) == 3 and k[0] == 'tags'] + [-1])

    for num, tag in zip(count(current_index+1), tags):
        data[('tags', num, 'name')] = tag

    for tag in tags:
        toolkit.get_validator('tag_length_validator')(tag, context)
        odsh_tag_name_validator(tag, context)


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
    plugins.implements(plugins.IPackageController, inherit=True)

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
                'odsh_get_resource_views': odsh_helpers.odsh_get_resource_views,
                'odsh_get_bounding_box': odsh_helpers.odsh_get_bounding_box,
                'odsh_get_spatial_text': odsh_helpers.odsh_get_spatial_text,
                'odsh_render_datetime': odsh_helpers.odsh_render_datetime,
                'odsh_upload_known_formats': odsh_helpers.odsh_upload_known_formats,
                'odsh_encodeurl': odsh_helpers.odsh_encodeurl,
                'odsh_extract_error': odsh_helpers.odsh_extract_error,
                'odsh_extract_value_from_extras': odsh_helpers.odsh_extract_value_from_extras,
                'odsh_create_checksum': odsh_helpers.odsh_create_checksum
                }

    def before_map(self, map):
        map.connect('info_page', '/info_page',
                    controller='ckanext.odsh.controller:OdshRouteController', action='info_page')
        map.connect('home', '/',
                    controller='ckanext.odsh.controller:OdshRouteController', action='start')

        # redirect all user routes to custom controller
        with SubMapper(map, controller='ckanext.odsh.controller:OdshUserController') as m:
            m.connect('/user/edit', action='edit')
            m.connect('user_generate_apikey',
                      '/user/generate_key/{id}', action='generate_apikey')
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

    def _update_schema(self, schema):
        for field in ['title', 'notes']:
            schema.update({field: [toolkit.get_converter('not_empty')]})

        for i, item in enumerate(schema['tags']['name']):
            if item == toolkit.get_validator('tag_name_validator'):
                schema['tags']['name'][i] = toolkit.get_validator(
                    'odsh_tag_name_validator')
        for i, item in enumerate(schema['tag_string']):
            if item == tag_string_convert:
                schema['tag_string'][i] = odsh_tag_string_convert

        schema['resources'].update({
            'url': [toolkit.get_converter('not_empty')],
            'format': [toolkit.get_converter('not_empty')]
        })

        schema['extras'].update({
            'key': [
                toolkit.get_converter('odsh_validate_issued'),
                toolkit.get_converter('odsh_validate_temporal_start'),
                toolkit.get_converter('odsh_validate_temporal_end'),
                toolkit.get_converter('known_spatial_uri'),
                toolkit.get_converter('licenseAttributionByText')
            ]
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
        return {'odsh_convert_groups_string': odsh_convert_groups_string,
                'licenseAttributionByText': odsh_delete_licenseAttributionByText_if_empty,
                'known_spatial_uri': known_spatial_uri,
                'odsh_validate_issued': odsh_validate_extra_date_factory('issued'),
                'odsh_validate_temporal_start': odsh_validate_extra_date_factory('temporal_start'),
                'odsh_validate_temporal_end': odsh_validate_extra_date_factory('temporal_end'),
                'odsh_tag_name_validator': odsh_tag_name_validator}


    # Add the custom parameters to Solr's facet queries
    # use several daterange queries agains temporal_start and temporal_end field
    # TODO: use field of type date_range in solr index instead
    def before_search(self, search_params):


        extras = search_params.get('extras')
        if not extras:
            # There are no extras in the search params, so do nothing.
            return search_params

        start_date=None
        end_date=None
        try:
            start_date = odsh_helpers.extend_search_convert_local_to_utc_timestamp(
                extras.get('ext_startdate'))
            end_date = odsh_helpers.extend_search_convert_local_to_utc_timestamp(
                extras.get('ext_enddate'))
        except:
            return search_params

        empty_range = start_date and end_date and start_date > end_date

        if not start_date and not end_date:
            return search_params

        do_enclosing_query = True
        if not start_date:
            do_enclosing_query = False
            start_date = '*'
        if not end_date:
            do_enclosing_query = False
            end_date = '*'

        fq = search_params['fq']

        start_query = '+extras_temporal_start:[{start_date} TO {end_date}]'.format(
            start_date=start_date, end_date=end_date)

        end_query = '+extras_temporal_end:[{start_date} TO {end_date}]'.format(
            start_date=start_date, end_date=end_date)

        enclosing_query = ''
        if do_enclosing_query and not empty_range:
            enclosing_query_start = 'extras_temporal_start:[* TO {start_date}]'.format(
                start_date=start_date)

            enclosing_query_end = 'extras_temporal_end:[{end_date} TO *]'.format(
                end_date=end_date)

            enclosing_query = ' OR ({enclosing_query_start} AND {enclosing_query_end})'.format(
                enclosing_query_start=enclosing_query_start, enclosing_query_end=enclosing_query_end)

        
        if end_date is '*':
            open_end_query = '(*:* NOT extras_temporal_end:[* TO *])'
        else:
            open_end_query = '((*:* NOT extras_temporal_end:[* TO *]) AND extras_temporal_start:[* TO {end_date}])'.format(
                    end_date=end_date)

        fq = '{fq} ({start_query} OR {end_query} {enclosing_query} OR {open_end_query})'.format(
            fq=fq, start_query=start_query, end_query=end_query, enclosing_query=enclosing_query, open_end_query=open_end_query)

        # fq = '{fq} ({start_query}'.format(
        #     fq=fq, start_query=start_query, end_query=end_query, enclosing_query=enclosing_query)

        # return modified facet queries
        search_params['fq'] = fq

        return search_params

    def before_index(self, dict_pkg):
        # make special date fields solr conform
        fields = ["issued", "temporal_start", "temporal_end"]
        for field in fields:
            field = 'extras_' + field
            if field in dict_pkg and dict_pkg[field]:
                d = parse(dict_pkg[field])
                dict_pkg[field] = '{0.year:4d}-{0.month:02d}-{0.day:02d}T00:00:00Z'.format(
                    d)
        return dict_pkg
