import logging
import ckan.logic as logic
from ckan.logic.action.update import user_update
from ckan.logic.action.create import package_create, user_create, group_member_create
import ckan.model as model
import ckan.lib.dictization.model_dictize as model_dictize
from ckan.lib.munge import munge_title_to_name
import ckan.plugins.toolkit as toolkit
from ckan.lib.search.common import (
    make_connection, SearchError, SearchQueryError
)
import pysolr
import datetime

log = logging.getLogger(__name__)


def odsh_package_create(context, data_dict):
    pkg_type = data_dict.get('type', None)
    if pkg_type == 'collection':
        return package_create(context, data_dict)
    munge_increment_name(data_dict)
    if pkg_type != 'dataset':
        return package_create(context, data_dict)
    issued = False
    for extra in data_dict.get('extras'):
        if extra['key'] == 'issued':
            issued = True
            break
    if not issued:
        data_dict['extras'].append({'key': 'issued', 'value': datetime.datetime.utcnow().isoformat()})
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
