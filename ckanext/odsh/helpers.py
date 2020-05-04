# encoding: utf-8

import logging
import traceback
import ast
import ckan.plugins.toolkit as toolkit
import ckan.logic as logic
import ckan.model as model
import ckan.logic.action as action
import ckan.lib.helpers as helpers
import json
from ckan.common import c
import datetime
from dateutil import parser
from ckan.common import config
import urllib
import hashlib
import re
import csv
import urllib2
from ckan.common import request
import pdb
from urlparse import urlsplit, urlunsplit
import subprocess
import ckan.lib.helpers as helpers

get_action = logic.get_action
log = logging.getLogger(__name__)


def odsh_openness_score_dataset_html(dataset):
    score = -1 
    #dataset = json.loads(dataset)
    resources = dataset.get('resources')
    if resources is None:
        return score 
    for resource in resources:
        r_qa = resource.get('qa')
        if r_qa:
            try:
                qa = None
                # r_qa might be a string of a dictionary when 'dataset' is send from solr
                if isinstance(r_qa, basestring):
                    qa = ast.literal_eval(r_qa)
                else:
                    qa = r_qa
                resource_score = qa.get('openness_score')
                if resource_score > score:
                    score = resource_score
            except AttributeError, e:
                log.error('Error while calculating openness score %s: %s\nException: %s',
                          e.__class__.__name__,  unicode(e), traceback.format_exc())
    return score


def odsh_get_resource_details(resource_id):
    resource_details = toolkit.get_action('resource_show')(
        data_dict={'id': resource_id})
    return resource_details


def odsh_get_resource_views(pkg_dict, resource):

    context = {'model': model, 'session': model.Session,
               'user': c.user, 'for_view': True,
               'auth_user_obj': c.userobj}
    return get_action('resource_view_list')(
        context, {'id': resource['id']})


def odsh_get_bounding_box(pkg_dict):
    try:
        extras = pkg_dict.get('extras')
        spatial = None
        for f in extras:
            if 'key' in f and f['key'] == 'spatial':
                spatial = f['value']
                break

        if spatial is not None:
            d = json.loads(spatial)
            if 'coordinates' in d:
                coords = d['coordinates']
                return compute_bounding_box(coords)
    except Exception, e:
        log.error('Error while bounding box %s: %s\nException: %s',
                  e.__class__.__name__,  unicode(e), traceback.format_exc())
    return None


def compute_bounding_box(coords):
    if len(coords) == 0:
        return None

    coords = [c for sublist in coords for c in sublist]
    if type(coords[0][0]) == list:
        # multipolygon
        coords = [c for sublist in coords for c in sublist]

    minx = min(coords, key=lambda t: t[0])[0]
    maxx = max(coords, key=lambda t: t[0])[0]
    miny = min(coords, key=lambda t: t[1])[1]
    maxy = max(coords, key=lambda t: t[1])[1]

    return [maxx, minx, maxy, miny]


def odsh_get_spatial_text(pkg_dict):
    extras = pkg_dict.get('extras')
    spatial = None
    if extras is None:
        return None
    for f in extras:
        if 'key' in f and f['key'] == 'spatial_text':
            spatial = f['value']
            return spatial
    return None

def extend_search_convert_local_to_utc_timestamp(str_timestamp):
    if not str_timestamp:
        return None 

    if not re.match(r'\d\d\d\d-\d\d-\d\d', str_timestamp):
        raise ValueError('wrong format')
    
    dt = parser.parse(str_timestamp, dayfirst=False).isoformat()

    return dt+"Z"

def odsh_render_datetime(datetime_, fromIso=True):
    date_format='{0.day:02d}.{0.month:02d}.{0.year:04d}'
    if not datetime_:
        return ''
    if not re.match(r'\d\d\d\d-\d\d-\d\d', datetime_):
        return ''
    try:
        if fromIso:
            DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
        else:
            DATETIME_FORMAT = '%Y-%m-%d'

        dt = parser.parse(datetime_, dayfirst=False)
        return date_format.format(dt)

    except:
        return ''

def odsh_upload_known_formats():
    value = config.get('ckanext.odsh.upload_formats', [])
    value = toolkit.aslist(value)
    return value

def odsh_tracking_id():
    return config.get('ckanext.odsh.matomo_id')

def odsh_tracking_url():
    return config.get('ckanext.odsh.matomo_url')

def odsh_encodeurl(url):
    return urllib.quote(url, safe='')


def odsh_create_checksum(in_string):
    hashstring = hashlib.md5(in_string.encode('utf-8')).hexdigest()
    return int(hashstring, base=16)


def odsh_extract_error(key, errors, field='extras'):
    if not errors or not (field in errors):
        return None
    ext = errors[field]
    for item in ext:
        if 'key' in item:
            for error in item['key']:
                if error.startswith(key):
                    return error

def odsh_extract_error_new(key, errors):
    if not errors or not ('__extras' in errors):
        return None
    error = errors['__extras'][0].get(key,None)
    if error:
        return key + ': ' + error

def odsh_extract_value_from_extras(extras, key):
    if not extras:
        return None
    for item in extras:
        if 'key' in item and item['key'].lower() == key.lower():
            if 'value' in item:
                return item['value']
            return None


def presorted_license_options(existing_license_id=None):
    '''Returns [(l.title, l.id), ...] for the licenses configured to be
    offered. Always includes the existing_license_id, if supplied.
    '''
    register = model.Package.get_license_register()
    licenses = register.values()
    license_ids = [license.id for license in licenses]
    if existing_license_id and existing_license_id not in license_ids:
        license_ids.insert(0, existing_license_id)
    return [('','')]+[
        (license_id,
         register[license_id].title if license_id in register else license_id)
        for license_id in license_ids]


def odsh_has_more_facets(facet, limit=None, exclude_active=False):
    facets = []
    for facet_item in c.search_facets.get(facet)['items']:
        if not len(facet_item['name'].strip()) or facet_item['count']==0:
            continue
        if not (facet, facet_item['name']) in request.params.items():
            facets.append(dict(active=False, **facet_item))
        elif not exclude_active:
            facets.append(dict(active=True, **facet_item))
    if c.search_facets_limits and limit is None:
        limit = c.search_facets_limits.get(facet)
    if limit is not None and len(facets) > limit:
        return True
    return False


def odsh_public_url():
    return config.get('ckanext.odsh.public_url')

def spatial_extends_available():

    mapping_file = config.get('ckanext.odsh.spatial.mapping')
    try:
        mapping_file = urllib2.urlopen(mapping_file)
    except Exception:
        raise Exception("Could not load spatial mapping file!")

    spatial_text = str()
    spatial = str()
    cr = csv.reader(mapping_file, delimiter="\t")
    result = []
    for row in cr:
        spatial_text = row[1]
        result.append(spatial_text.decode('UTF-8'))
    return result

def odsh_public_resource_url(res):
    home = config.get('ckanext.odsh.public_url')
    if res.get('url_type',None) == 'upload' and 'url' in res:
        f = urlsplit(res['url'])
        return urlunsplit((0, 0, f[2], f[3], f[4]))
    else:
        return res['url']

def odsh_get_version_id():
    try:
        home = config.get('ckanext.odsh.home', None)
        if home:
            if home[-1] == '/':
                home = home[:-1]
            home += '/.git'
            return subprocess.check_output(["git", "--git-dir", home, "rev-parse", "HEAD"]).strip()
    except:
        return 'unknown'
    return 'unknown'

def odsh_show_testbanner():
    return config.get('ckanext.odsh.showtestbanner', 'False') == 'True'

def odsh_is_slave():
    c = config.get('ckanext.odsh.slave', None)
    if c is None or (c != 'True' and c != 'False'):
        return -1 
    return 1 if c == 'True' else 0


def odsh_get_facet_items_dict(name, limit=None):
    '''
    Gets all facets like 'get_facet_items_dict' but sorted alphabetically
    instead by count.
    '''
    if name == 'groups':
        limit = 20
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


def odsh_remove_route(map, routename):
    route = None
    for i, r in enumerate(map.matchlist):

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


def is_within_last_month(date, date_ref=None):
    '''
    date is a datetime.date object containing the date to be checked
    date_ref is a datetime.date object containing the reference date
    if date_ref is not specified, the date of today is used
    this method is needed by the method OdshPlugin.before_view in plugin.py
    '''
    
    if not date_ref:
        date_ref = datetime.date.today()
    
    [year_ref, month_ref, day_ref] = [date_ref.year, date_ref.month, date_ref.day]

    try:
        if month_ref > 1:
            one_month_ago = datetime.date(year_ref, month_ref-1, day_ref)
        else:
            one_month_ago = datetime.date(year_ref-1, 12, day_ref)
    except ValueError:
        # this happens if month before month_ref has less days than month_ref
        one_month_ago = datetime.date(year_ref, month_ref, 1) - datetime.timedelta(days=1)
    
    if date > one_month_ago:
        return True
    return False

def tpsh_get_all_datasets_belonging_to_collection(context, collection_name):
    rel_collection_dict = dict({"id": collection_name})
    name_list = list()
    try:
        list_rel_collection = get_action('package_relationships_list')(context, rel_collection_dict)
    except AssertionError:
        #if there does not exist an relationship, returns an empty list
        return name_list 
    for item in list_rel_collection:
        item_object = item.get('object') 
        name_list.append(item_object)
    return name_list

def tpsh_get_all_datasets_belonging_to_collection_by_dataset(context, dataset_name):
    collection_name = tpsh_get_collection_name_by_dataset(context, dataset_name)
    if collection_name:
        name_list = tpsh_get_all_datasets_belonging_to_collection(context, collection_name)
        return name_list
    return list()

def tpsh_get_collection_name_by_dataset(context, dataset_name):
    rel_dataset_dict = dict({"id" : dataset_name})
    list_rel_dataset = toolkit.get_action('package_relationships_list')(context, rel_dataset_dict)
    if not len(list_rel_dataset):
        return None    
    collection_name = list_rel_dataset[0]['object']
    return collection_name

def tpsh_get_successor_and_predecessor_dataset(context, pkg_dict):
    dataset_name = pkg_dict.get('name')
    siblings_dicts_with_access = _get_siblings_dicts_with_access(context, pkg_dict)
    if siblings_dicts_with_access:
        n_siblings = len(siblings_dicts_with_access)
        siblings_dicts_sorted_by_date_issued = _sort_siblings_by_name_and_date(siblings_dicts_with_access)
        siblings_names_sorted_by_date_issued = [d['name'] for d in siblings_dicts_sorted_by_date_issued]
        id_current_dataset = siblings_names_sorted_by_date_issued.index(dataset_name)
        predecessor_name = (
            siblings_names_sorted_by_date_issued[id_current_dataset-1] if (id_current_dataset > 0) 
            else None
        )
        successor_name = (
            siblings_names_sorted_by_date_issued[id_current_dataset+1] if (id_current_dataset < n_siblings-1) 
            else None
        )
    else:
        predecessor_name, successor_name = None, None
    return successor_name, predecessor_name

def _get_siblings_dicts_with_access(context, pkg_dict):
    dataset_name = pkg_dict.get('name')
    list_of_siblings = tpsh_get_all_datasets_belonging_to_collection_by_dataset(context, dataset_name)
    n_siblings = len(list_of_siblings)
    if n_siblings>0:
        siblings_dicts = [get_package_dict(name) for name in list_of_siblings]
        user_has_access = lambda pkg_dict:helpers.check_access('package_show', pkg_dict)
        siblings_dicts_with_access = filter(user_has_access, siblings_dicts)
        return siblings_dicts_with_access
    return None

    
def _sort_siblings_by_name_and_date(siblings_dicts):
    '''
    sort by name first and then by date to have a fallback if dates are the same
    '''
    _get_name = lambda pkg_dict:pkg_dict.get('name')
    _get_issued = lambda pkg_dict:odsh_extract_value_from_extras(pkg_dict.get('extras'), 'issued')
    siblings_dicts_sorted_by_name = sorted(siblings_dicts, key=_get_name)
    siblings_dicts_sorted_by_date_issued = sorted(siblings_dicts_sorted_by_name, key=_get_issued)
    return siblings_dicts_sorted_by_date_issued


def get_package_dict(name):
    return model.Package.get(name).as_dict()

def tpsh_get_successor_and_predecessor_urls(context, pkg_dict):
    successor_name, predecessor_name = tpsh_get_successor_and_predecessor_dataset(context, pkg_dict)
    successor_url, predecessor_url = (
        helpers.url_for(controller='package', action='read', id=name)
        if name is not None
        else None
        for name in (successor_name, predecessor_name)
    )
    return successor_url, predecessor_url

def short_name_for_category(category_name):
    translations = {
        'soci': u'Bevölkerung',
        'educ': u'Bildung',
        'ener': u'Energie',
        'heal': u'Gesundheit',
        'intr': u'Internationales',
        'just': u'Justiz',
        'agri': u'Landwirtschaft',
        'gove': u'Regierung',
        'regi': u'Regionales',
        'envi': u'Umwelt',
        'tran': u'Verkehr',
        'econ': u'Wirtschaft',
        'tech': u'Wissenschaft',
    }
    return translations.get(category_name)
