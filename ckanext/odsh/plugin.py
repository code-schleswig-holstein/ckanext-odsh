import datetime
import json
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.lib.plugins import DefaultTranslation
from ckan.lib.plugins import DefaultDatasetForm
from ckan.logic.validators import tag_string_convert
from ckan.logic.schema import default_extras_schema
from ckan.common import OrderedDict
from ckanext.odsh.lib.uploader import ODSHResourceUpload
import ckan.lib.helpers as helpers
import helpers as odsh_helpers
import ckanext.odsh.logic.action as action
from ckanext.dcat.interfaces import IDCATRDFHarvester
from ckanext.dcatde.extras import Extras

from routes.mapper import SubMapper
from pylons import config
from dateutil.parser import parse
from ckan import model

import ckan.plugins as p

import logging
import validation
import precondition
 
import sys

log = logging.getLogger(__name__)

# from functools import wraps
# from flask import Flask, redirect, jsonify
# app = Flask(__name__)

# def get_http_exception_handler(app):
#     """Overrides the default http exception handler to return JSON."""
#     handle_http_exception = app.handle_http_exception
#     @wraps(handle_http_exception)
#     def ret_val(exception):
#         print("HEHREHR")
#         exc = handle_http_exception(exception)    
#         return jsonify({'code':exc.code, 'message':exc.description}), exc.code
#     return ret_val

# # Override the HTTP exception handler.
# app.handle_http_exception = get_http_exception_handler(app)


# def my_except_hook(exctype, value, traceback):
#     print('GOT excepton')
#     log.exception(value)
#     sys.__excepthook__(exctype, value, traceback)
# print('INSTALL EX')
# sys.excepthook = my_except_hook

_ = toolkit._

from multiline_formatter.formatter import MultilineMessagesFormatter
class OdshLogger(MultilineMessagesFormatter):
    multiline_marker = '...'
    multiline_fmt = multiline_marker + ' : %(message)s'

    def format(self, record):
        """
        This is mostly the same as logging.Formatter.format except for the splitlines() thing.
        This is done so (copied the code) to not make logging a bottleneck. It's not lots of code
        after all, and it's pretty straightforward.
        """
        endl_marker = '\n... : ";'
        record.message = record.getMessage()
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)
        if '\n' in record.message:
            splitted = record.message.splitlines()
            output = self._fmt % dict(record.__dict__, message=splitted.pop(0))
            output += ' ' + self.multiline_marker % record.__dict__ + '\n'
            output += '\n'.join(
                self.multiline_fmt % dict(record.__dict__, message=line)
                for line in splitted
            )
            output = output.replace('"','\\"')
            output += endl_marker
        else:
            output = self._fmt % record.__dict__

        if record.exc_info:
            # Cache the traceback text to avoid converting it multiple times
            # (it's constant anyway)
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            output += ' ' + self.multiline_marker % record.__dict__ + '\n'
            try:
                output += '\n'.join(
                    self.multiline_fmt % dict(record.__dict__, message=line)
                    for index, line in enumerate(record.exc_text.splitlines())
                )
                output = output.replace('"','\\"')
                output += endl_marker
            except UnicodeError:
                output += '\n'.join(
                    self.multiline_fmt % dict(record.__dict__, message=line)
                    for index, line
                    in enumerate(record.exc_text.decode(sys.getfilesystemencoding(), 'replace').splitlines())
                )
        return output


def odsh_get_facet_items_dict(name, limit=None):
    '''
    Gets all facets like 'get_facet_items_dict' but sorted alphabetically
    instead by count.
    '''
    facets = helpers.get_facet_items_dict(name, limit)
    facets.sort(key=lambda it: (it['display_name'].lower(), -it['count']))
    return facets


def odsh_main_groups():
    '''Return a list of the groups to be shown on the start page.'''

    # Get a list of all the site's groups from CKAN, sorted by number of
    # datasets.
    groups = toolkit.get_action('group_list')(
        data_dict={'all_fields': True})

    return groups


def odsh_now():
    return helpers.render_datetime(datetime.datetime.now(), "%Y-%m-%d")


def odsh_group_id_selected(selected, group_id):
    if type(selected) is not list:
        selected = [selected]
    for g in selected:
        if (isinstance(g, basestring) and group_id == g) or (type(g) is dict and group_id == g['id']):
            return True

    return False

def remove_route(map,routename):
    route = None
    for i,r in enumerate(map.matchlist):

        if r.name == routename:
            route = r
            break
    if route is not None:
        map.matchlist.remove(route)
        for key in map.maxkeys:
            if key == route.maxkeys:
                map.maxkeys.pop(key)
                map._routenames.pop(route.name)
                break


class OdshIcapPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IUploader, inherit=True)

    def get_resource_uploader(self, data_dict):
        return ODSHResourceUpload(data_dict)


class OdshAutocompletePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IActions)

    def get_actions(self):
        return {'autocomplete': action.autocomplete}


class OdshHarvestPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IConfigurer)

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'harvest_templates')
    plugins.implements(plugins.IRoutes, inherit=True)
    def before_map(self, map):
        DATASET_TYPE_NAME='harvest'
        controller = 'ckanext.odsh.controller:OdshHarvestController'

        map.connect('{0}_delete'.format(DATASET_TYPE_NAME), '/' + DATASET_TYPE_NAME + '/delete/:id',controller=controller, action='delete')
        map.connect('{0}_refresh'.format(DATASET_TYPE_NAME), '/' + DATASET_TYPE_NAME + '/refresh/:id',controller=controller,
                action='refresh')
        map.connect('{0}_admin'.format(DATASET_TYPE_NAME), '/' + DATASET_TYPE_NAME + '/admin/:id', controller=controller, action='admin')
        map.connect('{0}_about'.format(DATASET_TYPE_NAME), '/' + DATASET_TYPE_NAME + '/about/:id', controller=controller, action='about')
        map.connect('{0}_clear'.format(DATASET_TYPE_NAME), '/' + DATASET_TYPE_NAME + '/clear/:id', controller=controller, action='clear')

        map.connect('harvest_job_list', '/' + DATASET_TYPE_NAME + '/{source}/job', controller=controller, action='list_jobs')
        map.connect('harvest_job_show_last', '/' + DATASET_TYPE_NAME + '/{source}/job/last', controller=controller, action='show_last_job')
        map.connect('harvest_job_show', '/' + DATASET_TYPE_NAME + '/{source}/job/{id}', controller=controller, action='show_job')
        map.connect('harvest_job_abort', '/' + DATASET_TYPE_NAME + '/{source}/job/{id}/abort', controller=controller, action='abort_job')

        map.connect('harvest_object_show', '/' + DATASET_TYPE_NAME + '/object/:id', controller=controller, action='show_object')
        map.connect('harvest_object_for_dataset_show', '/dataset/harvest_object/:id', controller=controller, action='show_object', ref_type='dataset')

        org_controller = 'ckanext.harvest.controllers.organization:OrganizationController'
        map.connect('{0}_org_list'.format(DATASET_TYPE_NAME), '/organization/' + DATASET_TYPE_NAME + '/' + '{id}', controller=org_controller, action='source_list')
        return map

    def after_map(self, map):
        return map


class OdshDCATHarvestPlugin(plugins.SingletonPlugin):
    plugins.implements(IDCATRDFHarvester, inherit=True)

    def before_update(self, harvest_object, dataset_dict, temp_dict):
        
        existing_package_dict = self._get_existing_dataset(harvest_object.guid)
        new_dataset_extras = Extras(dataset_dict['extras'])
        if new_dataset_extras.key('modified') and \
          new_dataset_extras.value('modified') < existing_package_dict.get('metadata_modified'):
            log.info("Modified date of new dataset is not newer than "
            + "the already exisiting dataset, ignoring new one.") 
            dataset_dict.clear()

    def _get_existing_dataset(self, guid):
        '''
        Checks if a dataset with a certain guid extra already exists

        Returns a dict as the ones returned by package_show
        '''

        datasets = model.Session.query(model.Package.id) \
                                .join(model.PackageExtra) \
                                .filter(model.PackageExtra.key == 'guid') \
                                .filter(model.PackageExtra.value == guid) \
                                .filter(model.Package.state == 'active') \
                                .all()

        if not datasets:
            return None
        elif len(datasets) > 1:
            log.error('Found more than one dataset with the same guid: {0}'
                      .format(guid))

        return p.toolkit.get_action('package_show')({}, {'id': datasets[0][0]})


class OdshPlugin(plugins.SingletonPlugin, DefaultTranslation, DefaultDatasetForm):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IFacets)
    plugins.implements(plugins.IDatasetForm)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IActions)

    # IActions

    def get_actions(self):
        return {'package_create': action.odsh_package_create,
                'user_create': action.odsh_user_create}

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
                'odsh_extract_error_new': odsh_helpers.odsh_extract_error_new,
                'odsh_extract_value_from_extras': odsh_helpers.odsh_extract_value_from_extras,
                'odsh_create_checksum': odsh_helpers.odsh_create_checksum,
                'presorted_license_options': odsh_helpers.presorted_license_options,
                'odsh_tracking_id': odsh_helpers.odsh_tracking_id,
                'odsh_tracking_url': odsh_helpers.odsh_tracking_url,
                'odsh_has_more_facets': odsh_helpers.odsh_has_more_facets,
                'odsh_public_url': odsh_helpers.odsh_public_url,
                'odsh_spatial_extends_available': odsh_helpers.spatial_extends_available
                }

    def after_map(self, map):
        return map

    def before_map(self, map):
        map.connect('info_page', '/info_page',
                    controller='ckanext.odsh.controller:OdshRouteController', action='info_page')
        map.connect('home', '/',
                    controller='ckanext.odsh.controller:OdshRouteController', action='start')

        map.redirect('/dataset/{id}/resource/{resource_id}', '/dataset/{id}')

        if p.toolkit.asbool(config.get('ckanext.dcat.enable_rdf_endpoints', True)):
            remove_route(map, 'dcat_catalog')
            map.connect('dcat_catalog',
                            config.get('ckanext.dcat.catalog_endpoint', '/catalog.{_format}'),
                            controller='ckanext.odsh.controller:OdshDCATController', action='read_catalog',
                            requirements={'_format': 'xml|rdf|n3|ttl|jsonld'})

        # with SubMapper(map, controller='ckanext.odsh.controller:OdshApiController') as m:
        #     m.connect('/catalog2', action='read_catalog')



        # /api ver 3 or none with matomo
        GET_POST = dict(method=['GET', 'POST'])
        with SubMapper(map, controller='ckanext.odsh.controller:OdshApiController', path_prefix='/api{ver:/3|}', ver='/3') as m:
            m.connect('/action/{logic_function}', action='action', conditions=GET_POST)

        with SubMapper(map, controller='ckanext.odsh.controller:OdshFeedController') as m:
            m.connect('/feeds/custom.atom', action='custom')

        with SubMapper(map, controller='ckanext.odsh.controller:OdshPackageController') as m:
            m.connect('new_view', '/dataset/{id}/resource/{resource_id}/new_view', action='edit_view', ckan_icon='pencil-square-o')

        with SubMapper(map, controller='ckanext.odsh.controller:OdshGroupController') as m:
            m.connect('organizations_index', '/organization', action='index')

        # redirect all user routes to custom controller
        with SubMapper(map, controller='ckanext.odsh.controller:OdshUserController') as m:
            m.connect('user_index', '/user', action='index')
            m.connect('/user/edit', action='edit')
            m.connect('user_edit', '/user/edit/{id:.*}', action='edit', ckan_icon='cog')
            m.connect('user_delete', '/user/delete/{id}', action='delete')
            m.connect('/user/reset/{id:.*}', action='perform_reset')
            m.connect('/user/reset', action='request_reset')
            m.connect('register', '/user/register', action='register')
            m.connect('login', '/user/login', action='login')
            m.connect('/user/_logout', action='logout')
            m.connect('/user/logged_in', action='logged_in')
            m.connect('/user/logged_out', action='logged_out')
            m.connect('/user/logged_out_redirect', action='logged_out_page')
            m.connect('user_datasets', '/user/{id:.*}', action='read',
                      ckan_icon='sitemap')
        return map

    def dataset_facets(self, facets_dict, package_type):
        return OrderedDict({'organization': _('Herausgeber'),
                            'res_format': _('Dateiformat'),
                            'license_title': _('Lizenz'),
                            'groups': _('Kategorie'),
                            'openness': _('Open-Data-Eigenschaften')})

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
        for field in ['title', 'notes','license_id']:
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
        schema.update({'__extras':  [toolkit.get_converter('odsh_validate_extras')] })

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
        return validation.get_validators()

    # Add the custom parameters to Solr's facet queries
    # use several daterange queries agains temporal_start and temporal_end field
    # TODO: use field of type date_range in solr index instead
    def before_search(self, search_params):
        search_params['facet.mincount']=0
        extras = search_params.get('extras')
        print(search_params)
        if not extras:
            # There are no extras in the search params, so do nothing.
            return search_params

        fq = search_params['fq']

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

        fq = u'{fq} ({start_query} OR {end_query} {enclosing_query} OR {open_end_query})'.format(
            fq=fq, start_query=start_query, end_query=end_query, enclosing_query=enclosing_query, open_end_query=open_end_query)
        

        search_params['fq'] = fq

        return search_params

    scores = [ ['0OL'], ['0OL','1RE'], ['0OL','1RE','2OF'], ['0OL','1RE','2OF','3URI'], ['0OL','1RE','2OF','3URI','4LD']]
    def map_qa_score(self, dict_pkg):
        if 'validated_data_dict' in dict_pkg and 'openness_score' in dict_pkg['validated_data_dict']:
                d = json.loads(dict_pkg['validated_data_dict'])
                score = -1
                for r in d['resources']:
                    if 'qa' in r:
                        i = r['qa'].find('openness_score')
                        s = int(r['qa'][i+17])
                        if s > score:
                                score=s
                if score > 0:
                    dict_pkg['openness']=OdshPlugin.scores[score-1]


    #@precondition.not_on_slave
    def before_index(self, dict_pkg):
        # make special date fields solr conform
        fields = ["issued", "temporal_start", "temporal_end"]
        for field in fields:
            field = 'extras_' + field
            if field in dict_pkg and dict_pkg[field]:
                d = parse(dict_pkg[field])
                dict_pkg[field] = '{0.year:04d}-{0.month:02d}-{0.day:02d}T00:00:00Z'.format(d)
        # if 'res_format' in dict_pkg:
        #     dict_pkg['res_format']=[e.lower() for e in dict_pkg['res_format']]

        self.map_qa_score(dict_pkg)

        return dict_pkg

