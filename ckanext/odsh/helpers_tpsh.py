# encoding: utf-8

import csv
import datetime
import logging
from string import lower
import json
import re
import urllib2
from collections import OrderedDict
import subprocess
import os

from ckan.common import config
import ckan.lib.helpers as helpers
import ckan.logic.action.create as create
import ckan.model as model
import ckan.plugins.toolkit as toolkit


import ckanext.odsh.helpers as odsh_helpers

log = logging.getLogger(__name__)

CKAN_TYPES = {'http://dcat-ap.de/def/datasetTypes/collection': 'collection'}


def map_dct_type_to_ckan_type(dct_type):
    '''
    matches the field dct:type from a harvested rdf file 
    to the corresponding ckan package type
    '''
    ckan_type = CKAN_TYPES.get(dct_type)
    return ckan_type

def map_ckan_type_to_dct_type(ckan_type):
    DCT_TYPES = _revert_dict(CKAN_TYPES)
    dct_type = DCT_TYPES.get(ckan_type)
    return dct_type

def _revert_dict(d):
    d_inverse = {v: k for k, v in d.iteritems()}
    return d_inverse

def add_pkg_to_collection(id_pkg, id_collection):
    if id_pkg and id_collection:
        relationship_dict = {
            'subject': id_pkg,
            'object': id_collection,
            'type': 'child_of',
        }
        toolkit.get_action('package_relationship_create')(None, relationship_dict)

def use_matomo():
    '''Return the value of the use_matomo config setting.

    To enable using matomo, add this line to the
    [app:main] section of your CKAN config file::

      ckanext.odsh.use_matomo = True

    Returns ``False`` by default, if the setting is not in the config file.

    :rtype: bool

    '''
    value = config.get('ckanext.odsh.use_matomo', False)
    value = toolkit.asbool(value)
    return value

def correct_missing_relationship(pkg_dict, pkg_relationships_from_model):
    '''
    This function corrects missing relationship in show package.
    Note this fix is only good with one or non relationship. 
    This error is well known but was not fixed. https://github.com/ckan/ckan/issues/3114
    The error causes the deletation of relationships, because package_show is
    used in resource_create to get the package. 
    '''
    if pkg_relationships_from_model:
        relationship_from_model = pkg_relationships_from_model[0]
        relationship_list_from_dict = pkg_dict.get('relationships_as_subject')
        type_pkg = pkg_dict.get('type')
        needs_update = type_pkg == 'dataset' and not relationship_list_from_dict
        if needs_update:
            relationship_for_package = {
                '__extras': {
                    'object_package_id': relationship_from_model.object_package_id,
                    'revision_id': relationship_from_model.revision_id,
                    'subject_package_id': relationship_from_model.subject_package_id,
                },
                'comment': relationship_from_model.subject_package_id,
                'id': relationship_from_model.id,
                'type': relationship_from_model.type,
            }
            pkg_dict['relationships_as_subject'].append(relationship_for_package) 
    return pkg_dict

def get_pkg_relationships_from_model(pkg_dict):
    pkg_id = pkg_dict.get('id')
    return model.Package.get(pkg_id).get_relationships()

def load_language_mapping():
    with open(config.get('ckanext.odsh.language_mapping')) as language_mapping_json:
        LANGUAGE_MAPPING = json.loads(language_mapping_json.read())
    return LANGUAGE_MAPPING

def load_json_to_ordered_dict(json_str):
    return json.loads(json_str, object_pairs_hook=OrderedDict)

def load_subject_mapping():
    with open(config.get('ckanext.odsh.subject_mapping')) as subject_mapping_json:
        SUBJECT_MAPPING = load_json_to_ordered_dict(subject_mapping_json.read())
    return SUBJECT_MAPPING

def get_language_of_package(pkg_dict):
    LANGUAGE_MAPPING = load_language_mapping()
    language_id = _get_language_id(pkg_dict)
    if not language_id:
        return None
    language = LANGUAGE_MAPPING.get(language_id)
    return language

def get_language_icon(pkg_dict):
    ICONS = {
        "http://publications.europa.eu/resource/authority/language/DAN": '/base/images/icon_lang_danish.png',
        "http://publications.europa.eu/resource/authority/language/ENG": '/base/images/icon_lang_english.png',
    }
    language_id = _get_language_id(pkg_dict)
    if not language_id:
        return None
    return ICONS.get(language_id) 

def _get_language_id(pkg_dict):
    language_id = odsh_helpers.odsh_extract_value_from_extras(pkg_dict.get('extras'), 'language')
    language_id = pkg_dict.get('language')
    if not language_id:
        language_id = odsh_helpers.odsh_extract_value_from_extras(
            pkg_dict.get('extras'), 'language'
        )
    if not language_id:
        return None
    language_id_cleaned = re.sub('[\[\]\"]', '', language_id)
    return language_id_cleaned

def get_spatial_for_selection():
    mapping_path = config.get('ckanext.odsh.spatial.mapping')
    try:
        mapping_file = urllib2.urlopen(mapping_path)
    except urllib2.URLError:
        log.error('Could not load spatial mapping file')
        raise
    cr = csv.reader(mapping_file, delimiter="\t")
    spatial_mapping = list()
    for row in cr:
        key  = row[0].decode('UTF-8')
        value = row[1].decode('UTF-8')
        spatial_mapping.append({'key':key, 'value':value}) 
    spatial_mapping.append({'key':'', 'value':''})   
    return spatial_mapping

def get_subject_for_selection():
    SUBJECT_MAPPING = load_subject_mapping()
    dict_for_select_box = [{'key': 'empty', 'value':' '}, ]
    dict_for_select_box.extend(
        [{'key': key, 'value': SUBJECT_MAPPING[key]} for key in SUBJECT_MAPPING]
    )
    return dict_for_select_box

def get_language_for_selection():
    LANGUAGE_MAPPING = load_language_mapping()
    dict_for_select_box = [{'key': key, 'value': LANGUAGE_MAPPING[key]} for key in LANGUAGE_MAPPING]
    return dict_for_select_box

def get_package_dict(name):
    '''
    raises ckan.logic.NotFound if not found
    '''
    package_dict = toolkit.get_action('package_show')(None, {'id': name})
    return package_dict

def size_of_fmt(num, suffix='B'):
    for unit in ['',' k',' M',' G',' T',' P',' E',' Z']:
        if abs(num) < 1000.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1000.0
    return "%.1f%s%s" % (num, 'Y', suffix)

def get_resource_size(resource):
    resource_size = resource.get('size')
    if resource_size:
        return size_of_fmt(resource_size)    


def get_address_org(organization):
    list_extras = organization.get('extras')
    address = dict()
    if not list_extras:
        return address
    for extra in list_extras:
            address.update({extra.get('key'):extra.get('value')})
    web = address.get('web')
    if web and not web.startswith('http'):
         web = 'http://' + web
         address.update({'web':web})    
    return address


def get_body_mail(organization, package):
    package_name = package.get('name')
    url = helpers.url_for(controller='package', action='read', id=package_name, qualified = True)
    title = package.get('title')
    anrede = "Sehr geehrte Damen und Herren," + "%0D%0A" +  "%0D%0A" + "zu folgendem Eintrag habe ich eine Anmerkung/Frage:" + "%0D%0A" + "%0D%0A" 
    mail_titel = "Titel: " + title + "%0D%0A"    
    mail_document = "Dokument-ID: " +  package_name + "%0D%0A"
    mail_url = "URL: " +  url + "%0D%0A"  +  "%0D%0A" 
    message =  mail_titel + mail_document  +  mail_url + "Mein Kommentar:" +  "%0D%0A"    +  "%0D%0A"  +  "%0D%0A"  +  "%0D%0A" 
    return anrede + message
