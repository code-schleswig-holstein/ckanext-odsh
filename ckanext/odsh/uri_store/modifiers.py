import store 

import ckanext.odsh.helpers as odsh_helpers

def add_uri(dataset_dict):
    uri = odsh_helpers.odsh_extract_value_from_extras(
        dataset_dict.get('extras'), 'uri'
    )
    id = dataset_dict.get('id')
    store.uri_to_id.update({uri: id})

def get_id_from_uri(uri):
    id = store.uri_to_id.get(uri)
    return id

def _set_uri_to_id(new_uri_to_id):
    store.uri_to_id = new_uri_to_id

def _get_uri_to_id():
    return store.uri_to_id