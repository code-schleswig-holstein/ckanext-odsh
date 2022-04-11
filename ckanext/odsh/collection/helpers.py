from string import lower
from operator import itemgetter

import ckan.lib.helpers as helpers
import ckan.model as model
import ckan.plugins.toolkit as toolkit


def get_collection(dataset_dict):
    collection_id = get_collection_id(dataset_dict)
    if collection_id:
        return get_collection_info(collection_id, dataset_dict)
    return None


def get_collection_info(collection_id, dataset_dict=None):
    collection_dict = get_package_dict(collection_id)
    if not collection_dict:
        return None
    dataset_names = get_dataset_names(collection_dict)
    if not dataset_names:
        return None
    datasets_in_collection = get_datasets_from_solr(dataset_names)
    collection_info = gather_collection_info(collection_dict, datasets_in_collection, dataset_dict)
    return collection_info


def get_collection_id(dataset_dict):
    relationships_dataset = dataset_dict.get('relationships_as_subject')
    if relationships_dataset and len(relationships_dataset):        
        return relationships_dataset[0]['__extras']['object_package_id']
    relationships_dataset = dataset_dict.get('relationships')
    if relationships_dataset and len(relationships_dataset):
        return relationships_dataset[0].get('object')
    return None


def get_package_dict(name):
    package = model.Package.get(name)
    if package:
        return package.as_dict()
    else:
        return None


def get_dataset_names(collection_dict):
    if not collection_dict:
        return []
    collection_dict = get_package_dict(collection_dict.get('id')) # needed to get full package_dict
    if collection_dict:
        relationships_collection = collection_dict.get('relationships')
        names_collection_members = [relationship.get('object') for relationship in relationships_collection]
        return names_collection_members
    else:
        return []


def get_datasets_from_solr(dataset_names):
    context = None

    if not dataset_names:
        return []

    name_expression = ' OR '.join(dataset_names)
    fq = 'name:({})'.format(name_expression)
    
    sort = 'extras_issued asc'
    
    # maximum possible number of results is 1000, 
    # see https://docs.ckan.org/en/ckan-2.7.3/api/index.html#ckan.logic.action.get.package_search
    query_result = toolkit.get_action('package_search')(context, {
        'fq': fq,
        'sort': sort,
        'rows': 1000, 
    })

    results = query_result.get('results')
    datasets_found = results if results else []

    return datasets_found


def gather_collection_info(collection_dict, datasets_in_collection, dataset_dict=None):
    url_collection = url_from_id(collection_dict.get('name'))

    if not datasets_in_collection:
        return {
            'title': collection_dict.get('title'),
            'url': url_collection,
            'members': []
        }

    name_first_dataset = datasets_in_collection[0].get('name')
    url_first_dataset = url_from_id(name_first_dataset)
    
    name_last_dataset = datasets_in_collection[-1].get('name')
    url_last_dataset = url_from_id(name_last_dataset)

    name_collection = collection_dict.get('name')
    persistent_link_last_member = url_last_member(name_collection)


    if dataset_dict:
        name_current_dataset = dataset_dict.get('name')
        dataset_names = [d.get('name') for d in datasets_in_collection]
        
        def get_predecessor():
            try:
                id_current = dataset_names.index(name_current_dataset)
            except ValueError:
                return None
            if id_current > 0:
                return dataset_names[id_current - 1]
            return None
        
        def get_successor():
            try:
                id_current = dataset_names.index(name_current_dataset)
            except ValueError:
                return None
            if id_current < len(dataset_names) - 1:
                return dataset_names[id_current + 1]
            return None
        
        name_predecessor = get_predecessor()
        url_predecessor = url_from_id(name_predecessor) if name_predecessor else None
        
        name_successor = get_successor()
        url_successor = url_from_id(name_successor) if name_successor else None
    else:
        url_predecessor = url_successor = None
    
    return {
        'title': collection_dict.get('title'),
        'url': url_collection,
        'members': datasets_in_collection,
        'first_member': {
            'name': name_first_dataset,
            'url': url_first_dataset,
        },
        'last_member': {
            'name': name_last_dataset,
            'url': url_last_dataset,
        },
        'predecessor': {
            'url': url_predecessor,
        },
        'successor': {
            'url': url_successor,
        },
        'persistent_link_last_member': persistent_link_last_member,
    }

def url_from_id(package_id):
    return helpers.url_for(controller='package', action='read', id=package_id)

def url_last_member(name_collection):
    return helpers.url_for(
        controller='ckanext.odsh.collection.controller:LatestDatasetController', 
        action='latest',
        id=name_collection
    )


def get_latest_dataset(collection_name):
    collection_info = get_collection_info(collection_name)
    if not collection_info:
        return None
    latest_name = collection_info['last_member']['name']
    return latest_name


def get_latest_resources_for_format(collection_name, resource_format):
    collection_info = get_collection_info(collection_name)
    members = collection_info.get('members')
    if not members:
        return None
    latest_dataset = members[-1]
    resources = latest_dataset.get('resources')
    if not resources:
        return None
    resources_with_asked_type = [r for r in resources if r.get('format').upper() == resource_format.upper()]
    resources_sorted = sorted(resources_with_asked_type, key=itemgetter('id','created'), reverse=True)
    return resources_sorted[-1]
