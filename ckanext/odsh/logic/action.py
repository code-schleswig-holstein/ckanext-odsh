import logging
from ckan.logic.action.create import package_create
import ckan.model as model

log = logging.getLogger(__name__)


def odsh_package_create(context, data_dict):
    log.debug('in ODSH package_create')
    munge_increment_name(data_dict)
    return package_create(context, data_dict)

def munge_increment_name(data_dict):
    log.debug('IN MUNGE')
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
