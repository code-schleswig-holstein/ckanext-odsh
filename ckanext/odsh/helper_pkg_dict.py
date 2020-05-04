import re

import ckanext.odsh.helpers as helpers_odsh
import datetime

import ckanext.odsh.helpers_tpsh as helpers_tpsh
import ckanext.odsh.collection.helpers as helpers_collection

import ckanext.odsh.uri_store as uri_store

from ckanext.odsh.pretty_daterange.date_range_formatter import DateRangeFormatter

import logging
log = logging.getLogger(__name__)


class HelperPgkDict(object):
    '''
    a convenience class for all operations related to pkg_dict
    aka dataset_dict, dict_pkg ...
    '''
    def __init__(self, pkg_dict):
        self.pkg_dict = pkg_dict
    
    def is_collection(self):
        '''
        return True if self.pkg_dict['type'] is collection,
        false otherwise
        '''
        dataset_type = self.pkg_dict.get(u'type')
        return dataset_type == 'collection'
    
    def shall_be_part_of_collection(self):
        '''
        return the flag 'add_to_collection',
        this one is set by ODSHDCATdeProfile._mark_for_adding_to_ckan_collection
        '''
        shall_be_part_of_collection = self.pkg_dict.get('add_to_collection')
        return shall_be_part_of_collection
    
    def update_relations_to_collection_members(self):
        '''
        update a collection's relationships to its members

        '''

        id_collection = self.pkg_dict.get('id')
        uris_collection_members = self.get_uris_collection_members()
        ckan_ids_collection_members = [self.get_id_from_store(uri) for uri in uris_collection_members]
        for id_pkg in ckan_ids_collection_members:
            helpers_tpsh.add_pkg_to_collection(id_pkg, id_collection)
            log.info('Added package with id {} to collection with id {}'.format(id_pkg, id_collection))
    
    def get_uris_collection_members(self):
        '''
        get the uris of a collection's members
        
        Returns:
            list of uris taken from the 'has_version' in in self.pkg_dict['extras']
        '''
        extras = self.pkg_dict.get('extras')
        uris_collection_members_as_string = helpers_odsh.odsh_extract_value_from_extras(
            extras, 'has_version'
        )
        uris_collection_members_as_string_cleaned = re.sub(
            r'[\"\[\] ]',
            '',
            uris_collection_members_as_string,
            0, 0,
        )
        uris_collection_members = uris_collection_members_as_string_cleaned.split(',')
        return uris_collection_members

    
    def update_relation_to_collection(self):
        '''
        update a package's relation to its collection
        '''
        id_pkg = self.pkg_dict.get('id')
        uri_collection = self.get_collection_uri()
        id_collection = uri_store.get_id_from_uri(uri_collection)
        helpers_tpsh.add_pkg_to_collection(id_pkg, id_collection)
        log.info('Added package with id {} to collection with id {}'.format(id_pkg, id_collection))
    

    def get_collection_uri(self):
        '''
        return the collection uri stored in 'extras
        '''
        extras = self.pkg_dict.get('extras')
        uri_collection = helpers_odsh.odsh_extract_value_from_extras(
            extras, 'is_version_of'
        )
        if uri_collection:
            uri_collection_cleaned = re.sub(
                r'[\"\[\] ]',
                '',
                uri_collection,
                0, 0,
            )
            return uri_collection_cleaned
        return None
    

    def get_collection_id(self):
        '''
        construct a collection uri from the id of 
        the containing collection
        '''
        package_name = self.pkg_dict.get('name')
        collection_name = helpers_collection.get_collection_name_by_dataset(package_name)
        collection_dict = helpers_collection.get_package_dict(collection_name)
        collection_id = collection_dict.get('id')
        return collection_id

    
    def add_uri_to_store(self):
        '''
        store pair of uri and id for subsequent use
        '''
        uri_store.add_uri(self.pkg_dict)
    
    @staticmethod
    def get_id_from_store(uri):
        '''
        get id from known uri
        '''
        id = uri_store.get_id_from_uri(uri)
        return id

    def is_package_new(self):
        date_package_created_as_str = self._get_date_of_package_creation_from_pkg_dict()
        if date_package_created_as_str == None:
            is_new = False
        else:
            date_package_created = self._get_date_from_string(date_package_created_as_str)
            if date_package_created == None:
                is_new = False
            else:
                is_new = helpers_odsh.is_within_last_month(date_package_created)
        return is_new
    
    def _get_date_of_package_creation_from_pkg_dict(self):
        if 'extras' in self.pkg_dict:
            extras = self.pkg_dict['extras']
            issued = helpers_odsh.odsh_extract_value_from_extras(extras=extras, key='issued') # is None if issued not in extras
            return issued
        else:
            return None
        
    @staticmethod
    def _get_date_from_string(date_time_str):
        date_time_format = '%Y-%m-%dT%H:%M:%S' #e.g. u'2019-06-12T11:56:25'
        try:
            date_time = datetime.datetime.strptime(date_time_str, date_time_format)
            date = date_time.date()
        except (ValueError, TypeError):
            # if date cannot be converted from string return None
            date = None
        return date

    def get_prettified_daterange(self):
        date_start, date_end = self._get_date_start_and_end_from_pkg_dict()
        prettified_daterange = self._construct_prettified_daterange(date_start, date_end)
        return prettified_daterange
    
    @staticmethod
    def _construct_prettified_daterange(date_start, date_end):
        try:
            prettified_daterange = DateRangeFormatter(date_start, date_end).get_formatted_str()
        except ValueError as err:
            log.warning(err.message)
            return '-'
        return prettified_daterange
    
    def _get_date_start_and_end_from_pkg_dict(self):
        if 'extras' in self.pkg_dict:
            extras = self.pkg_dict['extras']
            date_start_as_str, date_end_as_str = (
                helpers_odsh.odsh_extract_value_from_extras(
                    extras=extras, key=key)
                for key in ('temporal_start', 'temporal_end')
            )
            date_start = self._get_date_from_string(date_start_as_str)
            date_end = self._get_date_from_string(date_end_as_str)
        else:
            date_start = None
            date_end = None
        return date_start, date_end


def get_daterange_prettified(pkg_dict):
    '''
    wrapper function to use as a template helper
    '''
    daterange_prettified = HelperPgkDict(pkg_dict).get_prettified_daterange()
    return daterange_prettified