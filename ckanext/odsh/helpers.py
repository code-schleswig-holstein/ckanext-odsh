import logging
import traceback
import ast
import ckan.plugins.toolkit as toolkit
import ckan.logic as logic
import ckan.model as model
import json
from ckan.common import c
import datetime
from dateutil import parser
from ckan.common import config
import urllib
import hashlib
import re

get_action = logic.get_action
log = logging.getLogger(__name__)


def odsh_openness_score_dataset_html(dataset):
    score = 0
    #dataset = json.loads(dataset)
    resources = dataset.get('resources')
    if resources is None:
        return 0
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
        raise 'wrong format'
    
    dt = parser.parse(str_timestamp, dayfirst=False).isoformat()

    return dt+"Z"

def odsh_render_datetime(datetime_, fromIso=True):
    date_format='{0.day:02d}.{0.month:02d}.{0.year:4d}'
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
                    return error.replace(key+':', '')

def odsh_extract_error_new(key, errors):
    print('ERRORS')
    print(errors)
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