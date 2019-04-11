import logging
from ckan.logic.action.create import package_create, user_create, group_member_create
import ckan.model as model
import ckan.lib.dictization.model_dictize as model_dictize
import ckan.plugins.toolkit as toolkit
from ckan.lib.search.common import (
    make_connection, SearchError, SearchQueryError
)
import pysolr

log = logging.getLogger(__name__)


def odsh_package_create(context, data_dict):
    munge_increment_name(data_dict)
    return package_create(context, data_dict)


def munge_increment_name(data_dict):
    from ckan.lib.munge import munge_title_to_name

    name_base = name = munge_title_to_name(data_dict['title'])
    pkg = model.Package.get(name)
    i = 0
    while pkg:
        i += 1
        name = name_base + str(i)
        pkg = model.Package.get(name)
    log.debug('name: %s' % name)
    data_dict['name'] = name


def odsh_user_create(context, data_dict):
    model = context['model']
    user = user_create(context, data_dict)
    groups = toolkit.get_action('group_list')(data_dict={'all_fields': False})
    for group in groups:
        group_member_create(context, {'id': group, 'username': user.get('name'), 'role': 'member'})
    return model_dictize.user_dictize(model.User.get(user.get('name')), context)


@toolkit.side_effect_free
def autocomplete(context, data_dict):
    query = {
        'spellcheck.q': data_dict['q'],
        'wt': 'json'}

    conn = make_connection(decode_dates=False)
    log.debug('Suggest query: %r' % query)
    try:
        solr_response = conn.search('', search_handler='suggest', **query)
    except pysolr.SolrError as e:
        raise SearchError('SOLR returned an error running query: %r Error: %r' %
                          (query, e))

    suggest = solr_response.raw_response.get('spellcheck')
    return suggest
