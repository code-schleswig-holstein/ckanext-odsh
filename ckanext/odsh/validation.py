# This Python file uses the following encoding: utf-8
import logging
import unicodecsv as csv
import re
import urllib2
import json
from itertools import count
from dateutil.parser import parse
from pylons import config

import ckan.plugins.toolkit as toolkit
import ckan.model as model
from ckan.lib.navl.dictization_functions import Missing

from ckanext.odsh.helpers_tpsh import get_package_dict

_ = toolkit._

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
    error_message_no_group = 'at least one group needed'
    if value != None:
        # 'value != None' means the extra key 'groups' was found,
        # so the dataset came from manual editing via the web-frontend.
        if not value:
            if requireAtLeastOne:
                errors['groups'] = error_message_no_group
            data[('groups', 0, 'id')] = ''
            return

        groups = [g.strip() for g in value.split(',') if value.strip()]
        for k in data.keys():
            if len(k) == 3 and k[0] == 'groups':
                data[k] = ''
                # del data[k]
        if len(groups) == 0:
            if requireAtLeastOne:
                errors['groups'] = error_message_no_group
            return

        for num, group in zip(range(len(groups)), groups):
            data[('groups', num, 'id')] = group
    else:  # no extra-field 'groups'
        # dataset might come from a harvest process
        if not data.get(('groups', 0, 'id'), False) and \
           not data.get(('groups', 0, 'name'), False):
            errors['groups'] = error_message_no_group


def validate_extras(key, data, errors, context):
    extra_errors = {}
    
    isStaNord = ('id',) in data and data[('id',)][:7] == 'StaNord'
    is_optional_temporal_start = toolkit.asbool(
        config.get('ckanext.odsh.is_optional_temporal_start', False)
    ) or isStaNord

    require_at_least_one_category = toolkit.asbool(
        config.get('ckanext.odsh.require_at_least_one_category', False)
    )
    validate_extra_groups(
        data=data, 
        requireAtLeastOne=require_at_least_one_category, 
        errors=extra_errors
    )
    
    is_date_start_before_date_end(data, extra_errors)
    
    validate_extra_date_new(
        key=key,
        field='issued',
        data=data,
        optional=isStaNord,
        errors=extra_errors
    )
    validate_extra_date_new(
        key=key,
        field='temporal_start',
        data=data,
        optional=is_optional_temporal_start, 
        errors=extra_errors
    )
    validate_extra_date_new(
        key=key,
        field='temporal_end',
        data=data,
        optional=True,
        errors=extra_errors
    )

    if len(extra_errors.values()):
        raise toolkit.Invalid(extra_errors)

def is_date_start_before_date_end(data, extra_errors):
    start_date = _extract_value(data, 'temporal_start')
    end_date = _extract_value(data, 'temporal_end')
    if start_date and end_date:
        if start_date > end_date:
            extra_errors['temporal_start'] = extra_errors['temporal_end'] = 'Please enter a valid period of time.'

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

    if not value:
        if not optional:
            errors[field] = 'empty'
        return
    else:
        if re.match(r'\d\d\d\d-\d\d-\d\d', value):
            try:
                dt = parse(value)
                _set_value(data, field, dt.isoformat())
                return
            except ValueError:
                pass
        errors[field] = 'not a valid date'


def validate_licenseAttributionByText(key, data, errors, context):
    register = model.Package.get_license_register()
    isByLicense = False
    for k in data:
        if len(k) > 0 and k[0] == 'license_id' and data[k] and not isinstance(data[k], Missing) and \
                'Namensnennung' in register[data[k]].title:
            isByLicense = True
            break
    hasAttribution = False
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
    if data.get(('__extras',)) and 'spatial_uri_temp' in data.get(('__extras',)):
        _copy_spatial_uri_temp_to_extras(data)
    value = _extract_value(data, 'spatial_uri')
    require_spatial_uri = toolkit.asbool(
        config.get('ckanext.odsh.require_spatial_uri', False)
    )
    error_message_spatial_uri_empty = 'spatial_uri: empty not allowed'

    if not value:
        poly = None

        # some harvesters might import a polygon directly...
        poly = _extract_value(data, 'spatial')

        has_old_uri = False
        pkg = context.get('package', None)
        if pkg:
            old_uri = pkg.extras.get('spatial_uri', None)
            has_old_uri = old_uri != None and len(old_uri) > 0
            if not poly:
                poly = pkg.extras.get('spatial', None)
        if (not poly) and require_spatial_uri:
            raise toolkit.Invalid(error_message_spatial_uri_empty)
        if has_old_uri and require_spatial_uri:
            raise toolkit.Invalid(error_message_spatial_uri_empty)
        else:
            if poly:
                new_index = next_extra_index(data)
                data[('extras', new_index+1, 'key')] = 'spatial'
                data[('extras', new_index+1, 'value')] = poly
            return

    mapping_file = config.get('ckanext.odsh.spatial.mapping')
    try:
        mapping_file = urllib2.urlopen(mapping_file)
    except Exception:
        raise Exception("Could not load spatial mapping file!")

    not_found = True
    spatial_text = str()
    spatial = str()
    cr = csv.reader(mapping_file, delimiter="\t", encoding='utf-8')
    for row in cr:
        if row[0] == value:
            not_found = False
            spatial_text = row[1]
            loaded = json.loads(row[2])
            spatial = json.dumps(loaded['geometry'])
            break
    if not_found:
        raise toolkit.Invalid(
            'spatial_uri: uri unknown')

    new_index = next_extra_index(data)

    data[('extras', new_index, 'key')] = 'spatial_text'
    data[('extras', new_index, 'value')] = spatial_text
    data[('extras', new_index+1, 'key')] = 'spatial'
    data[('extras', new_index+1, 'value')] = spatial


def _copy_spatial_uri_temp_to_extras(data):
    '''
    copy the field spatial_uri_temp or
    spatial_url_temp originating 
    from the user interface to extras
    '''
    spatial_uri = data.get(('__extras',)).get('spatial_uri_temp')
    if spatial_uri is None:
        spatial_uri = data.get(('__extras',)).get('spatial_url_temp')
    is_spatial_uri_in_extras = _extract_value(data, 'spatial_uri') is not None
    if not is_spatial_uri_in_extras:
        next_index = next_extra_index(data)
        data[('extras', next_index, 'key')] = 'spatial_uri'
        data[('extras', next_index, 'value')] = spatial_uri
    else:
        _set_value(data, 'spatial_uri', spatial_uri)
    

def next_extra_index(data):
    current_indexes = [k[1] for k in data.keys()
                       if len(k) > 1 and k[0] == 'extras']

    return max(current_indexes) + 1 if current_indexes else 0


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


def _convert_subjectID_to_subjectText(subject_id, flattened_data):

    if not subject_id:
        return flattened_data

    default_subject_mapping_file_path = '/usr/lib/ckan/default/src/ckanext-odsh/subject_mapping.json'
    subject_mapping_file_path = config.get(
        'ckanext.odsh.subject_mapping_file_path', default_subject_mapping_file_path)
    
    try:
        with open(subject_mapping_file_path) as mapping_json:
             subject_mapping = json.loads(mapping_json.read())
    except IOError as err:
        log.error(
            'Could not load subject mapping file from {}'
            .format(subject_mapping_file_path)
        )
        raise
    except ValueError as err:
        log.error(
            'Could not convert subject mapping file from json. \nSubject mapping file: {}'
            .format(subject_mapping_file_path)
        )
        raise
    
    try: 
        subject_text = subject_mapping[subject_id]
    except:
        raise toolkit.Invalid(_('Subject must be a known URI.'))
        log.warning(
            'Subject_id "{}" not found in subject mapping dictionary.\nSubject mapping file: {}'
            .format(subject_id, subject_mapping_file_path)
        )
        

    new_index = next_extra_index(flattened_data)
    flattened_data[('extras', new_index, 'key')] = 'subject_text'
    flattened_data[('extras', new_index, 'value')] = subject_text
    return flattened_data


def validate_subject(key, flattened_data, errors, context):
    subject_id = flattened_data[key]
    require_subject = toolkit.asbool(
        config.get('ckanext.odsh.require_subject', True)
    )
    if not require_subject:
        flattened_data = _convert_subjectID_to_subjectText(subject_id, flattened_data)
        return
    if not subject_id:
        raise toolkit.Invalid(_('Subject must not be empty.'))
    flattened_data = _convert_subjectID_to_subjectText(subject_id, flattened_data)

def validate_relatedPackage(data):
    if data:
        try:
            get_package_dict(data)
        except logic.NotFound:
            raise toolkit.Invalid("relatedPackage: package '{}' not found".format(data))

def get_validators():
    return {
        'known_spatial_uri': known_spatial_uri,
        'odsh_tag_name_validator': tag_name_validator,
        'odsh_validate_extras': validate_extras,
        'validate_licenseAttributionByText': validate_licenseAttributionByText,
        'tpsh_validate_subject': validate_subject,
	'tpsh_validate_relatedPackage': validate_relatedPackage,
    }
