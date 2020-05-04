from string import lower

import ckan.lib.helpers as helpers
import ckan.model as model
import ckan.plugins.toolkit as toolkit



#routine functions

def get_package_dict(name):
    return model.Package.get(name).as_dict()

def get_relationships(name):
    collection_dict = get_package_dict(name)
    return collection_dict.get('relationships')

def get_all_datasets_belonging_to_collection(collection_name):
    list_rel_collection = get_relationships(collection_name)
    name_list = list()
    for item in list_rel_collection:
        item_object = item.get('object') 
        name_list.append(item_object)
    return name_list

#for mapping latest resources and latest dataset

def get_latest_dataset(collection_name):
    collection_list_relationships = get_all_datasets_belonging_to_collection(collection_name)
    latest_issued = latest_name = None
    for item in collection_list_relationships:
        item_pkt_dict =  get_package_dict(item)
        if helpers.check_access('package_show', item_pkt_dict):
            item_issued = item_pkt_dict.get('extras').get('issued')
            if latest_issued < item_issued or (latest_issued == item_issued and latest_name < item):
                latest_name=item
                latest_issued=item_issued
    return latest_name


def is_latest_resources(resource_format, type, resource_created,latest_created, resource_id, latest_id):
    if lower(resource_format) == lower(type):
        return (resource_created > latest_created or (resource_created == latest_created and resource_id > latest_id))
    else:
        return False

def get_latest_resources_for_type(collection_name, type):
    latest_dataset_name = get_latest_dataset(collection_name)
    latest_dataset = get_package_dict(latest_dataset_name)
    resource_list = latest_dataset.get('resources')
    latest_resource = latest_created = latest_id = None
    for resource in resource_list:
        resource_format = resource.get('format')
        resource_created = resource.get('created')
        resource_id = resource.get('id')
        if is_latest_resources(resource_format, type, resource_created, latest_created, resource_id, latest_id):
            latest_id=resource_id
            latest_created=resource_created
            latest_resource=resource
    return latest_resource

#for predecessor and successor



def get_collection_name_by_dataset(dataset_name):
    list_rel_dataset = get_relationships(dataset_name)
    if len(list_rel_dataset):        
        return list_rel_dataset[0]['object']

def get_collection_title_by_dataset(pkg_dict_dataset):
    dataset_name = pkg_dict_dataset.get('name')
    collection_name = get_collection_name_by_dataset(dataset_name)
    if not collection_name:
        return None
    context = None
    pkg_dict_collection = toolkit.get_action('package_show')(context, {'id': collection_name})
    if not pkg_dict_collection:
        return None
    title_collection = pkg_dict_collection.get('title')
    return title_collection

def get_all_datasets_belonging_to_collection_by_dataset(dataset_name):
    collection_name = get_collection_name_by_dataset(dataset_name)
    if collection_name: 
        return get_all_datasets_belonging_to_collection(collection_name)
    return []

def _get_siblings_dicts_with_access(pkg_dict):
    dataset_name = pkg_dict.get('name')
    list_of_siblings = get_all_datasets_belonging_to_collection_by_dataset(dataset_name)
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
    _get_issued = lambda pkg_dict:pkg_dict.get('extras').get('issued')
    siblings_dicts_sorted_by_name = sorted(siblings_dicts, key=_get_name)
    siblings_dicts_sorted_by_date_issued = sorted(siblings_dicts_sorted_by_name, key=_get_issued)
    return siblings_dicts_sorted_by_date_issued

def get_successor_and_predecessor_dataset(pkg_dict):
    dataset_name = pkg_dict.get('name')
    siblings_dicts_with_access = _get_siblings_dicts_with_access(pkg_dict)
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

def get_successor_and_predecessor_urls(pkg_dict):
    successor_name, predecessor_name = get_successor_and_predecessor_dataset(pkg_dict)
    successor_url, predecessor_url = (
        helpers.url_for(controller='package', action='read', id=name)
        if name is not None
        else None
        for name in (successor_name, predecessor_name)
    )
    return successor_url, predecessor_url

def get_successor(pkg_dict):
    successor_and_predecessor = get_successor_and_predecessor_urls(pkg_dict)
    return successor_and_predecessor[0]
    
def get_predecessor(pkg_dict):
    successor_and_predecessor = get_successor_and_predecessor_urls(pkg_dict)
    return successor_and_predecessor[1]

#link to latest collection member
def latest_collection_member_persistent_link(pkg_dict):
    dataset_name = pkg_dict.get('name')
    collection_name = get_collection_name_by_dataset(
        dataset_name=dataset_name
    )
    if not collection_name:
        return None
    url = helpers.url_for(
        controller='ckanext.odsh.collection.controller:LatestDatasetController', 
        action='latest',
        id=collection_name
    )
    return url