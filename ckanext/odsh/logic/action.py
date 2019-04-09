import logging
from ckan.logic.action.create import package_create, user_create, group_member_create
import ckan.model as model
import ckan.lib.dictization.model_dictize as model_dictize
import ckan.plugins.toolkit as toolkit

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