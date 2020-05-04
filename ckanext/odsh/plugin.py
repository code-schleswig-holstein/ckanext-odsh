# import from third parties
from dateutil.parser import parse
import json
import logging
from multiline_formatter.formatter import MultilineMessagesFormatter
import os
from pylons import config
from routes.mapper import SubMapper
import sys

# imports from ckan
from ckan.common import OrderedDict
import ckan.lib.helpers as helpers
from ckan.lib.plugins import DefaultTranslation, DefaultDatasetForm
from ckan.logic.validators import tag_string_convert
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.model as model

# imports from this extension
import ckanext.odsh.helpers as odsh_helpers
import ckanext.odsh.helpers_tpsh as helpers_tpsh
import ckanext.odsh.helper_pkg_dict as helper_pkg_dict
from helper_pkg_dict import HelperPgkDict
import ckanext.odsh.logic.action as action
import ckanext.odsh.validation as validation
import ckanext.odsh.search as search
from ckanext.odsh.odsh_logger import OdshLogger
import ckanext.odsh.tools as tools


log = logging.getLogger(__name__)

_ = toolkit._

class OdshPlugin(plugins.SingletonPlugin, DefaultTranslation, DefaultDatasetForm):
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IDatasetForm)
    plugins.implements(plugins.IFacets)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IResourceController, inherit=True)

    
    # IActions

    def get_actions(self):
        return {'package_create': action.odsh_package_create,
                'user_update':action.tpsh_user_update,
                'user_create': action.odsh_user_create}

    
    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'odsh')


    # IDatasetForm

    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []

    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return True
    
    def create_package_schema(self):
        schema = super(OdshPlugin, self).create_package_schema()
        self._update_schema(schema)
        self._tpsh_update_create_or_update_package_schema(schema)
        return schema

    def update_package_schema(self):
        schema = super(OdshPlugin, self).update_package_schema()
        self._update_schema(schema)
        self._tpsh_update_create_or_update_package_schema(schema)
        return schema

    def show_package_schema(self):
        schema = super(OdshPlugin, self).show_package_schema()
        self._tpsh_update_show_package_schema(schema)
        return schema

    def _update_schema(self, schema):
        for field in ['title', 'license_id']:
            schema.update({field: [toolkit.get_converter('not_empty')]})
        
        for i, item in enumerate(schema['tags']['name']):
            if item == toolkit.get_validator('tag_name_validator'):
                schema['tags']['name'][i] = toolkit.get_validator(
                    'odsh_tag_name_validator')
        for i, item in enumerate(schema['tag_string']):
            if item == tag_string_convert:
                schema['tag_string'][i] = validation.tag_string_convert

        schema['resources'].update({
            'url': [toolkit.get_converter('not_empty')],
            'format': [toolkit.get_converter('not_empty')],
        })

        schema['extras'].update({
            'key': [
                toolkit.get_converter('known_spatial_uri'),
                toolkit.get_converter('validate_licenseAttributionByText'),
            ]
        })
        schema.update(
            {'__extras':  [toolkit.get_converter('odsh_validate_extras')]})

    def _tpsh_update_create_or_update_package_schema(self, schema):
        schema.update({
            'language': [
                toolkit.get_validator('ignore_missing'),
                toolkit.get_converter('convert_to_extras')
            ],
            'thumbnail': [
                toolkit.get_validator('ignore_missing'),
                toolkit.get_converter('convert_to_extras')
            ],

        })
        return schema
    
    def _tpsh_update_show_package_schema(self, schema):
        schema.update({
            'language': [
                toolkit.get_converter('convert_from_extras'),
                toolkit.get_validator('ignore_missing')
            ],
            'thumbnail': [
                toolkit.get_converter('convert_from_extras'),
                toolkit.get_validator('ignore_missing')
            ],
        })
        return schema


    # IFacets
    
    def dataset_facets(self, facets_dict, package_type):
        return OrderedDict({'organization': _('Herausgeber'),
                            'groups': _('Kategorie'),
                            'res_format': _('Dateiformat'),
                            'license_title': _('Lizenz'),
                            'tags': _('Tags'),
                            'openness': _('Open-Data-Eigenschaften')
                            })

    def group_facets(self, facets_dict, group_type, package_type):
        return OrderedDict({'organization': _('Herausgeber'),
                            'res_format': _('Dateiformat'),
                            'license_title': _('Lizenz'),
                            'groups': _('Kategorie')})

    def organization_facets(self, facets_dict, organization_type, package_type):
        return OrderedDict({'organization': _('Herausgeber'),
                            'res_format': _('Dateiformat'),
                            'license_title': _('Lizenz'),
                            'groups': _('Kategorie')})
    

    # IPackageController

    def after_show(self, context, pkg_dict):
        '''
        corrects missing relationships in pkg dict
        adds the following key-value-pairs to pkg_dict:
        # key: 'is_new', value: True if the dataset has been created within the last month
        '''
        pkg_dict = helpers_tpsh.correct_missing_relationship(
            pkg_dict,
            helpers_tpsh.get_pkg_relationships_from_model(pkg_dict)
        )
        self._update_is_new_in_pkg_dict(pkg_dict)
        
        return pkg_dict

    def before_view(self, pkg_dict):
        '''
        adds the following key-value-pairs to pkg_dict:
        # key: 'is_new', value: True if the dataset has been created within the last month
        '''
        self._update_is_new_in_pkg_dict(pkg_dict)
        return pkg_dict
    
    def after_create(self, context, resource):
        if resource.get('package_id'):
            tools.add_attributes_resources(context, resource)

    def after_update(self, context, resource):
        if resource.get('package_id'):
            tools.add_attributes_resources(context, resource)

    @staticmethod
    def _update_is_new_in_pkg_dict(pkg_dict):
        is_new = HelperPgkDict(pkg_dict).is_package_new()
        pkg_dict.update({'is_new': is_new})

    
    def before_index(self, dict_pkg):
        # make special date fields solr conform
        fields = ["issued", "temporal_start", "temporal_end"]
        for field in fields:
            field = 'extras_' + field
            if field in dict_pkg and dict_pkg[field]:
                d = parse(dict_pkg[field])
                dict_pkg[field] = '{0.year:04d}-{0.month:02d}-{0.day:02d}T00:00:00Z'.format(
                    d)

        self.map_qa_score(dict_pkg)

        return dict_pkg
    

    # IRoutes
    
    def before_map(self, map):
        map.connect(
            'info_page', 
            '/info_page',
            controller='ckanext.odsh.controller:OdshRouteController', 
            action='info_page'
        )
        map.connect(
            'home', 
            '/',
            controller='ckanext.odsh.controller:OdshRouteController', 
            action='start'
        )

        map.redirect('/dataset/{id}/resource/{resource_id}', '/dataset/{id}')         

        if plugins.toolkit.asbool(config.get('ckanext.dcat.enable_rdf_endpoints', True)):
            odsh_helpers.odsh_remove_route(map, 'dcat_catalog')
            map.connect(
                'dcat_catalog',
                config.get(
                    'ckanext.dcat.catalog_endpoint',
                    '/catalog.{_format}'
                ),
                controller='ckanext.odsh.controller:OdshDCATController', 
                action='read_catalog',
                requirements={'_format': 'xml|rdf|n3|ttl|jsonld'}
            )

        # /api ver 3 or none with matomo
        GET_POST = dict(method=['GET', 'POST'])
        with SubMapper(
            map, 
            controller='ckanext.odsh.controller:OdshApiController', 
            path_prefix='/api{ver:/3|}', 
            ver='/3'
        ) as m:
            m.connect('/action/{logic_function}',
                      action='action', conditions=GET_POST)

        with SubMapper(map, controller='ckanext.odsh.controller:OdshFeedController') as m:
            m.connect('/feeds/custom.atom', action='custom')

        with SubMapper(map, controller='ckanext.odsh.controller:OdshPackageController') as m:
            m.connect('new_view', '/dataset/{id}/resource/{resource_id}/new_view',
                      action='edit_view', ckan_icon='pencil-square-o')

        with SubMapper(map, controller='ckanext.odsh.controller:OdshGroupController') as m:
            m.connect('organizations_index', '/organization', action='index')

        # redirect all user routes to custom controller
        with SubMapper(map, controller='ckanext.odsh.controller:OdshUserController') as m:
            m.connect('user_index', '/user', action='index')
            m.connect('/user/edit', action='edit')
            m.connect(
                'user_edit', '/user/edit/{id:.*}', action='edit', ckan_icon='cog')
            m.connect('user_delete', '/user/delete/{id}', action='delete')
            m.connect('/user/reset/{id:.*}', action='perform_reset')
            m.connect('/user/reset', action='request_reset')
            m.connect('register', '/user/register', action='register')
            m.connect('login', '/user/login', action='login')
            m.connect('/user/_logout', action='logout')
            m.connect('/user/logged_in', action='logged_in')
            m.connect('/user/logged_out', action='logged_out')
            m.connect('/user/logged_out_redirect', action='logged_out_page')
            m.connect('user_datasets', '/user/{id:(?!(generate_key|activity)).*}', action='read',
                      ckan_icon='sitemap')

        map.connect(
            'comment_datarequest', 
            '/datarequest/new',
            controller='ckanext.datarequests.controllers.ui_controller:DataRequestsUI',
            action='new', 
            conditions=dict(method=['GET', 'POST']), 
            ckan_icon='comment'
        )
        map.connect(
            'comment_datarequest', 
            '/datarequest/{id}',
            controller='ckanext.datarequests.controllers.ui_controller:DataRequestsUI',
            action='comment', 
            conditions=dict(method=['GET', 'POST']), 
            ckan_icon='comment'
        )
        return map
    
    def after_map(self, map):
        return map


    # ITemplateHelpers
    
    def get_helpers(self):
        # Template helper function names should begin with the name of the
        # extension they belong to, to avoid clashing with functions from
        # other extensions.
        return {'odsh_main_groups': odsh_helpers.odsh_main_groups,
                'odsh_now': odsh_helpers.odsh_now,
                'odsh_group_id_selected': odsh_helpers.odsh_group_id_selected,
                'odsh_get_facet_items_dict': odsh_helpers.odsh_get_facet_items_dict,
                'odsh_openness_score_dataset_html': odsh_helpers.odsh_openness_score_dataset_html,
                'odsh_get_resource_details': odsh_helpers.odsh_get_resource_details,
                'odsh_get_resource_views': odsh_helpers.odsh_get_resource_views,
                'odsh_get_bounding_box': odsh_helpers.odsh_get_bounding_box,
                'odsh_get_spatial_text': odsh_helpers.odsh_get_spatial_text,
                'odsh_render_datetime': odsh_helpers.odsh_render_datetime,
                'odsh_upload_known_formats': odsh_helpers.odsh_upload_known_formats,
                'odsh_encodeurl': odsh_helpers.odsh_encodeurl,
                'odsh_extract_error': odsh_helpers.odsh_extract_error,
                'odsh_extract_error_new': odsh_helpers.odsh_extract_error_new,
                'odsh_extract_value_from_extras': odsh_helpers.odsh_extract_value_from_extras,
                'odsh_create_checksum': odsh_helpers.odsh_create_checksum,
                'presorted_license_options': odsh_helpers.presorted_license_options,
                'odsh_tracking_id': odsh_helpers.odsh_tracking_id,
                'odsh_tracking_url': odsh_helpers.odsh_tracking_url,
                'odsh_has_more_facets': odsh_helpers.odsh_has_more_facets,
                'odsh_public_url': odsh_helpers.odsh_public_url,
                'odsh_spatial_extends_available': odsh_helpers.spatial_extends_available,
                'odsh_public_resource_url': odsh_helpers.odsh_public_resource_url,
                'odsh_get_version_id': odsh_helpers.odsh_get_version_id,
                'odsh_show_testbanner': odsh_helpers.odsh_show_testbanner,
                'odsh_is_slave': odsh_helpers.odsh_is_slave,
                'odsh_use_matomo': helpers_tpsh.use_matomo,
                'tpsh_get_daterange_prettified': helper_pkg_dict.get_daterange_prettified,
                'tpsh_get_language_of_package': helpers_tpsh.get_language_of_package,
                'get_language_icon': helpers_tpsh.get_language_icon,
                'short_name_for_category': odsh_helpers.short_name_for_category,
                'get_spatial_for_selection': helpers_tpsh.get_spatial_for_selection,
                'get_subject_for_selection': helpers_tpsh.get_subject_for_selection,
                'get_language_for_selection': helpers_tpsh.get_language_for_selection,
                'tpsh_get_resource_size': helpers_tpsh.get_resource_size,
                'tpsh_get_address_org':helpers_tpsh.get_address_org,
                'tpsh_get_body_mail':helpers_tpsh.get_body_mail,
                }

    
    # IValidators
    
    def get_validators(self):
        return validation.get_validators()

    # Add the custom parameters to Solr's facet queries
    # use several daterange queries agains temporal_start and temporal_end field
    # TODO: use field of type date_range in solr index instead
    def before_search(self, search_params):
        return search.before_search(search_params)

    scores = [['0OL'], ['0OL', '1RE'], ['0OL', '1RE', '2OF'], [
        '0OL', '1RE', '2OF', '3URI'], ['0OL', '1RE', '2OF', '3URI', '4LD']]

    def map_qa_score(self, dict_pkg):
        if 'validated_data_dict' in dict_pkg and 'openness_score' in dict_pkg['validated_data_dict']:
            d = json.loads(dict_pkg['validated_data_dict'])
            score = -1
            for r in d['resources']:
                if 'qa' in r:
                    i = r['qa'].find('openness_score')
                    s = int(r['qa'][i+17])
                    if s > score:
                        score = s
            if score > 0:
                dict_pkg['openness'] = OdshPlugin.scores[score-1]




