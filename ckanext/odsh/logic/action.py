import ckan.logic as logic
from ckan.logic.action.update import user_update
from ckan.logic.action.create import package_create, resource_create, user_create, group_member_create
import ckan.model as model
import ckan.lib.dictization.model_dictize as model_dictize
from ckan.lib.munge import munge_title_to_name
import ckan.plugins.toolkit as toolkit
from ckan.lib.search.common import make_connection, SearchError
import pysolr
import datetime
import cgi
import urllib2

import logging
log = logging.getLogger(__name__)

from ckanext.odsh.setup_proxy import setup_proxy, clear_proxy
from ckanext.odsh.collection.helpers import get_collection_id, get_package_dict
from ckanext.odsh.helpers_tpsh import add_pkg_to_collection
from ckanext.odsh.helpers import odsh_extract_value_from_extras


def odsh_package_create(context, data_dict):
    pkg_type = data_dict.get('type', None)
    if pkg_type == 'collection':
        return package_create(context, data_dict)
    munge_increment_name(data_dict)
    related_package_name = data_dict.get('relatedPackage')
    if related_package_name:
        new_package = package_create(context, data_dict)
        add_to_same_collection(related_package_name, new_package['name'])
        return new_package
    if pkg_type != 'dataset':
        return package_create(context, data_dict)
    add_issued_if_missing(data_dict)
    return package_create(context, data_dict)


def munge_increment_name(data_dict):
    title_from_dict = data_dict.get('title')
    if title_from_dict:
        name_base = name = munge_title_to_name(title_from_dict)
        pkg = model.Package.get(name)
        i = 0
        while pkg:
            i += 1
            name = name_base + str(i)
            pkg = model.Package.get(name)
        log.debug('name: %s' % name)
        data_dict['name'] = name

    
def add_issued_if_missing(data_dict):
    issued = odsh_extract_value_from_extras(data_dict.get('extras'), 'issued')
    if issued is None:
        data_dict['extras'].append({'key': 'issued', 'value': datetime.datetime.utcnow().isoformat()})
    

def add_to_same_collection(related_package_name, package_name):
    related_package = get_package_dict(related_package_name)
    collection_id = get_collection_id(related_package)
    if not collection_id:
        collection_dict = auto_create_collection(related_package)
        collection_id = collection_dict.get('id')
        add_to_collection(collection_id, related_package_name)
    add_to_collection(collection_id, package_name)


def auto_create_collection(related_package):
    related_package_title = related_package.get('title')
    owner_org = related_package.get('owner_org')
    _collection_dict = {
        'title': related_package_title,
        'owner_org': owner_org,
        'type': 'collection',
    }
    munge_increment_name(_collection_dict)
    collection_dict = package_create_via_toolkit(None, _collection_dict)
    return collection_dict


def package_create_via_toolkit(context, package_dict):
    return toolkit.get_action('package_create')(context, package_dict)


def add_to_collection(collection_id, package_name):
    add_pkg_to_collection(package_name, collection_id)


def check_password(password):
    return (len(password) >= 8 and
            any(c.islower() for c in password) and
            any(c.isupper() for c in password) and
            any((c.isalpha()==False) for c in password)) #Number or Special character


PASSWORD_ERROR_MESSAGE =  {'security': ['Passwort muss mindestens acht Zeichen, einen Gross-, einen Kleinbuchstaben und entweder eine Zahl oder ein Sondernzeichen enthalten!']}       


def odsh_user_create(context, data_dict):
    model = context['model']
    password = data_dict.get('password')
    if not password:
        password = data_dict.get('password1')
    if check_password(password):
        user = user_create(context, data_dict)
        groups = toolkit.get_action('group_list')(data_dict={'all_fields': False})
    
        for group in groups:
            group_member_create(context, {'id': group, 'username': user.get('name'), 'role': 'member'})
        return model_dictize.user_dictize(model.User.get(user.get('name')), context)
    else:
        raise logic.ValidationError(PASSWORD_ERROR_MESSAGE)          
  

def tpsh_user_update(context, data_dict):
      password = data_dict.get('password')
      if not password:
        password = data_dict.get('password1')
      if password and not check_password(password):
          raise logic.ValidationError(PASSWORD_ERROR_MESSAGE)      
      return user_update(context, data_dict)


@toolkit.side_effect_free
def autocomplete(context, data_dict):
    query = {
        'terms.prefix': data_dict['q'].lower(),
        'terms.limit': 20}

    conn = make_connection(decode_dates=False)
    log.debug('Suggest query: %r' % query)
    try:
        solr_response = conn.search('', search_handler='terms', **query)
    except pysolr.SolrError as e:
        raise SearchError('SOLR returned an error running query: %r Error: %r' %
                          (query, e))

    suggest = solr_response.raw_response.get("terms").get("suggest")
    suggestions = sorted(suggest, key=suggest.get, reverse=True)
    filtered_suggestions = []
    for suggestion in suggestions:
        suggestion = suggestion.replace("_", "").strip()
        filtered_suggestions.append(suggestion)
    final_suggestions = list(sorted(set(filtered_suggestions), key=filtered_suggestions.index))[:5]
    return final_suggestions


def odsh_resource_create(context, data_dict):
    is_linked_resource = not isinstance(data_dict['upload'], cgi.FieldStorage)
    if is_linked_resource:
        _download_linked_resource_to_tmp(data_dict['url'])
        _emulate_file_upload(data_dict)
    return resource_create(context, data_dict)

TMP_FILE_PATH = '/tmp/temp_file_upload'

def _download_linked_resource_to_tmp(url):
    log.debug('Downloading linked resource from {}.'.format(url))
    setup_proxy()
    test_file = urllib2.urlopen(url).read()
    clear_proxy()
    with open(TMP_FILE_PATH, 'wb') as temporary_file:
        temporary_file.write(test_file)

def _emulate_file_upload(data_dict):
    '''
    This function updates the data_dict in order to emulate
    the behaviour of resource creation with uploaded file for
    resource creation with link
    '''
    temporary_file = open(TMP_FILE_PATH, 'rb')
    upload_file = temporary_file
    filename = data_dict['name']
    upload = cgi.FieldStorage()
    upload.disposition = 'form-data'
    upload.disposition_options = {'filename': filename, 'name': 'upload'}
    upload.fp = upload_file
    upload.file = upload_file
    upload.type = 'application/pdf'
    upload.headers['content-type'] = upload.type
    upload.name = 'upload'
    upload.filename = filename
    data_dict['upload'] = upload