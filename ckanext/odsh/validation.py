# This Python file uses the following encoding: utf-8
import csv
import re
import urllib2
import json
from itertools import count
from dateutil.parser import parse

import ckan.plugins.toolkit as toolkit
import ckan.model as model
from ckan.lib.navl.dictization_functions import Missing

from pylons import config

_ = toolkit._

import logging
log = logging.getLogger(__name__)

def _extract_value(data, field):
    key = None
    for k in data.keys():
        if data[k] == field:
            key = k
            break
    if key is None:
        return None
    return data[(key[0], key[1], 'value')]

def validate_extra_groups(data, requireAtLeastOne, errors):
    value = _extract_value(data, 'groups')
    if value != None:
        # 'value != None' means the extra key 'groups' was found,
        # so the dataset came from manual editing via the web-frontend.        
        if not value:
            if requireAtLeastOne:
                errors['groups']= 'at least one group needed'
            data[('groups', 0, 'id')] = '' 
            return 

        groups = [g.strip() for g in value.split(',') if value.strip()]
        for k in data.keys():
            if len(k) == 3 and k[0] == 'groups':
                data[k]=''
                # del data[k]
        if len(groups)==0:
            if requireAtLeastOne:
                errors['groups']= 'at least one group needed'  
            return 

        for num, group in zip(range(len(groups)), groups):
            data[('groups', num, 'id')] = group
    else: # no extra-field 'groups'
        # dataset might come from a harvest process
        if not data.get(('groups', 0, 'id'), False) and \
           not data.get(('groups', 0, 'name'), False):
            errors['groups']= 'at least one group needed'

def validate_extras(key, data, errors, context):
    extra_errors = {}
    isStaNord = ('id',) in data and data[('id',)][:7] == 'StaNord'


    validate_extra_groups(data, True, extra_errors)
    validate_extra_date_new(key, 'issued', data, isStaNord, extra_errors)
    validate_extra_date_new(key, 'temporal_start', data, isStaNord, extra_errors)
    validate_extra_date_new(key, 'temporal_end', data, True, extra_errors)

    if len(extra_errors.values()):
        raise toolkit.Invalid(extra_errors)

def _set_value(data, field, value):
    key = None
    for k in data.keys():
        if data[k] == field:
            key = k
            break
    if key is None:
        return None
    data[(key[0], key[1], 'value')] = value

def validate_extra_date_new(key, field, data, optional, errors):
    value = _extract_value(data, field)

    print("DATE", value)

    if not value:
        if not optional:
            errors[field] = 'empty'
        return
    else:
        if re.match(r'\d\d\d\d-\d\d-\d\d', value):
            try:
                print ("BEOFRE PARSE", value)
                dt=parse(value)
                print("PARSED DATE", dt)
                _set_value(data, field, dt.isoformat())
                return
            except ValueError:
                print('ERROR from Exception')
                pass
        print('ERROR')
        errors[field] = 'not a valid date'

def validate_licenseAttributionByText(key, data, errors,context):
    register = model.Package.get_license_register()
    isByLicense=False
    for k in data:
        if len(k) > 0 and k[0] == 'license_id' and data[k] and not isinstance(data[k], Missing) and \
            'Namensnennung' in register[data[k]].title:
            isByLicense = True
            break
    hasAttribution=False
    for k in data:
        if data[k] == 'licenseAttributionByText':
            if isinstance(data[(k[0], k[1], 'value')], Missing) or (k[0], k[1], 'value') not in data:
                del data[(k[0], k[1], 'value')]
                del data[(k[0], k[1], 'key')]
                break
            else:
                value = data[(k[0], k[1], 'value')]
                hasAttribution = value != ''
                break
    if not hasAttribution:
        current_indexes = [k[1] for k in data.keys()
                           if len(k) > 1 and k[0] == 'extras']

        new_index = max(current_indexes) + 1 if current_indexes else 0
        data[('extras', new_index, 'key')] = 'licenseAttributionByText'
        data[('extras', new_index, 'value')] = ''

    if isByLicense and not hasAttribution:
        raise toolkit.Invalid(
            'licenseAttributionByText: empty not allowed')

    if not isByLicense and hasAttribution:
        raise toolkit.Invalid(
            'licenseAttributionByText: text not allowed for this license')


def known_spatial_uri(key, data, errors, context):
    value = _extract_value(data, 'spatial_uri')

    if not value:
        # some harvesters might import a polygon directly...
        poly = _extract_value(data, 'spatial')
        if not poly:
            raise toolkit.Invalid('spatial_uri: empty not allowed')
        else:
            return 
                
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
            'spatial_uri: uri unknown')

    # Get the current extras index
    current_indexes = [k[1] for k in data.keys()
                       if len(k) > 1 and k[0] == 'extras']

    new_index = max(current_indexes) + 1 if current_indexes else 0

    data[('extras', new_index, 'key')] = 'spatial_text'
    data[('extras', new_index, 'value')] = spatial_text
    data[('extras', new_index+1, 'key')] = 'spatial'
    data[('extras', new_index+1, 'value')] = spatial

def tag_name_validator(value, context):
    tagname_match = re.compile('[\w \-.\:\(\)\´\`]*$', re.UNICODE)
    if not tagname_match.match(value):
        raise toolkit.Invalid(_('Tag "%s" must be alphanumeric '
                                'characters or symbols: -_.:()') % (value))
    return value

def tag_string_convert(key, data, errors, context):
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
        tag_name_validator(tag, context)


def get_validators():
    return {
            'known_spatial_uri': known_spatial_uri,
            'odsh_tag_name_validator': tag_name_validator,
            'odsh_validate_extras':validate_extras,
            'validate_licenseAttributionByText':validate_licenseAttributionByText
            }
