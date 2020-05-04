# encoding: utf-8

import os
from collections import namedtuple, OrderedDict
import datetime
import nose.tools as nt
from mock import patch
from ckan.common import config
import ckan.logic.action.create as create
from ckanext.odsh.tests_tpsh.resources import org_dicts


from ckanext.odsh.helpers_tpsh import (
    map_dct_type_to_ckan_type,
    map_ckan_type_to_dct_type,
    add_pkg_to_collection,
    correct_missing_relationship,
    get_language_of_package,
    get_address_org,
    load_json_to_ordered_dict,
    load_subject_mapping,
    get_subject_for_selection
)


class TestMatchDctTypeToCkanType(object):
    
    def test_it_returns_collection(self):
        dct_type = 'http://dcat-ap.de/def/datasetTypes/collection'
        ckan_type = map_dct_type_to_ckan_type(dct_type)
        expected_ckan_type = 'collection'
        nt.assert_equal(ckan_type, expected_ckan_type)
    
    def test_it_returns_none_for_unknown_type(self):
        nt.assert_equal(
            map_dct_type_to_ckan_type('some unknown type'), 
            None
        )


class TestMatchCkanTypeToDctType(object):
    
    def test_it_returns_url_for_collection(self):
        ckan_type = 'collection'
        dct_type = map_ckan_type_to_dct_type(ckan_type)
        expected_dct_type = 'http://dcat-ap.de/def/datasetTypes/collection'
        nt.assert_equal(
            dct_type, expected_dct_type
        )


FakePackageRelationship = namedtuple(
    'FakePackageRelationship',
    '''
    object_package_id
    revision_id
    subject_package_id
    id
    type
    '''
)

class Test_correct_missing_relationship(object):
    def setUp(self):
        self.relationships_from_model = [
            FakePackageRelationship(
                object_package_id=u'object package id',
                revision_id=u'revision id',
                subject_package_id=u'subject package id',
                id=u'id',
                type=u'type'
            )
        ]

    def test_it_does_not_modify_pkg_dict_if_no_model_relationships(self):
        relationships_from_model = []
        original_pkg_dict = {'id': 'some_id'}
        pkg_dict = dict(original_pkg_dict)
        correct_missing_relationship(
            pkg_dict, relationships_from_model
        )
        nt.assert_equal(pkg_dict, original_pkg_dict)
    
    def test_it_does_not_modify_pkg_dict_if_relationships_already_in_dict(self):
        original_pkg_dict = {
            u'type': u'dataset',
            u'relationships_as_subject': [
                {
                    u'__extras': {
                        u'object_package_id': u'original object package id', 
                        u'revision_id': u'original revision id', 
                        u'subject_package_id': u'original subject package id'
                    }, 
                    u'comment': u'', 
                    u'id': u'original id', 
                    u'type': u'original type'
                }
            ]
        }
        pkg_dict = dict(original_pkg_dict)
        correct_missing_relationship(
            pkg_dict, self.relationships_from_model
        )
        nt.assert_equal(pkg_dict, original_pkg_dict)
    
    def test_it_does_not_modify_pkg_dict_if_type_collection(self):
        original_pkg_dict = {
            u'type': u'collection',
            u'relationships_as_subject': [
                {
                    u'__extras': {
                        u'object_package_id': u'original object package id', 
                        u'revision_id': u'original revision id', 
                        u'subject_package_id': u'original subject package id'
                    }, 
                    u'comment': u'', 
                    u'id': u'original id', 
                    u'type': u'original type'
                }
            ]
        }
        pkg_dict = dict(original_pkg_dict)
        correct_missing_relationship(
            pkg_dict, self.relationships_from_model
        )
        nt.assert_equal(pkg_dict, original_pkg_dict)
    
    def test_it_adds_relationships_if_not_already_in_dict(self):
        pkg_dict = {
            u'type': u'dataset',
            u'relationships_as_subject': []
        }
        correct_missing_relationship(
            pkg_dict, self.relationships_from_model
        )
        expected_pkg_dict = {
            u'type': u'dataset',
            u'relationships_as_subject': [
                {
                    u'__extras': {
                        u'object_package_id': u'object package id', 
                        u'revision_id': u'revision id', 
                        u'subject_package_id': u'subject package id'
                    }, 
                    u'comment': u'', 
                    u'id': u'id', 
                    u'type': u'type'
                }
            ]
        }

        from_relationships = lambda d, key: d.get('relationships_as_subject')[0].get(key)
        from_extras = lambda d, key: d.get('relationships_as_subject')[0].get('__extras').get(key)
        
        # assert
        nt.assert_equal(pkg_dict.get('type'), 'dataset')
        
        for key in ('id', 'type'):
            nt.assert_true(from_relationships(pkg_dict, key) is not None)
            nt.assert_equal(
                from_relationships(pkg_dict, key), 
                from_relationships(expected_pkg_dict, key)
            )

        for key in ('object_package_id', 'revision_id', 'subject_package_id'):
            nt.assert_true(
                pkg_dict is not None)
            nt.assert_equal(
                from_extras(pkg_dict, key),
                from_extras(expected_pkg_dict, key)
            )

    
class Test_get_language_of_package(object):
    def setUp(self):
        config.update({'ckanext.odsh.language_mapping': '/usr/lib/ckan/default/src/ckanext-odsh/language_mapping.json'})
    
    def tearDown(self):
        config.clear()

    def test_it_returns_Englisch(self):
        test_package = {
                'id': u'language_test',
                u'extras': [
                    {u'key': u'language', u'value': u'http://publications.europa.eu/resource/authority/language/ENG'},
                ]
            }
        nt.assert_equal(get_language_of_package(test_package),'Englisch')
    
    def test_it_returns_None_if_language_id_not_in_dict(self):
        test_package = {
                'id': u'language_test',
                u'extras': [
                    {u'key': u'language', u'value': u'tlhIngan Hol'},
                ]
            }
        nt.assert_equal(get_language_of_package(test_package), None)
    
    def test_it_returns_None_if_language_not_in_pkg_dict(self):
        test_package = {}
        nt.assert_equal(get_language_of_package(test_package), None)
    

class Test_get_address_org(object):
    def test_it_returns_address_for_org_with_address(self):
        organization = org_dicts.organization_with_address
        address = get_address_org(organization)
        nt.assert_equal(address.get('location'), u'Müllerdorf')
        nt.assert_equal(address.get('person'), u'Michael Müller')
        nt.assert_equal(address.get('mail'), u'mueller@mueller.de')
        nt.assert_equal(address.get('street'), u'Müllergasse 10')
        nt.assert_equal(address.get('telephone'), u'040 123456')
        nt.assert_equal(address.get('web'), u'http://mueller.de')

    def test_it_returns_empty_dict_if_called_via_organization_new(self):
        organization = dict()
        address = get_address_org(organization)
        assert type(address) is dict
        nt.assert_equal(len(address), 0)


def _add_subject_mapping_file_to_config():
    path_current_file = os.path.dirname(os.path.abspath(__file__))
    path_to_subject_mapping_file = path_current_file + '/resources/subject_mapping_for_tests.json'
    config.update({'ckanext.odsh.subject_mapping': path_to_subject_mapping_file})

class Test_load_json_to_ordered_dict(object):
    def setUp(self):
        json_str = '{"A": 1, "B": 2, "D": 3, "C":4, "E": 0}'
        self.result = load_json_to_ordered_dict(json_str)
    
    def test_it_does_not_crash(self):
        pass

    def test_it_returns_ordered_dict(self):
        nt.assert_is(type(self.result), OrderedDict)
    
    def test_it_preserves_order_of_keys(self):
        keys = self.result.keys()
        nt.assert_equal(keys, [u'A', u'B', u'D', u'C', u'E'])
    
    def test_it_preserves_order_of_values(self):
        values = self.result.values()
        nt.assert_equal(values, [1, 2, 3, 4, 0])

class Test_load_subject_mapping(object):
    def setUp(self):
        _add_subject_mapping_file_to_config()
        self.SUBJECT_MAPPING = load_subject_mapping()
    
    def tearDown(self):
        config.clear()
    
    def test_it_returns_an_ordered_dictionary(self):
        nt.assert_is(type(self.SUBJECT_MAPPING), OrderedDict)
    
    def test_it_preserves_order_of_json_file(self):
        keys = self.SUBJECT_MAPPING.keys()
        nt.assert_equal(keys[0], u'http://transparenz.schleswig-holstein.de/informationsgegenstand#Verwaltungsvorschrift')
        nt.assert_equal(keys[1], u'http://transparenz.schleswig-holstein.de/informationsgegenstand#Organisationsplan')
        nt.assert_equal(keys[2], u'http://transparenz.schleswig-holstein.de/informationsgegenstand#Geschaeftsverteilungsplan')
        nt.assert_equal(keys[3], u'http://transparenz.schleswig-holstein.de/informationsgegenstand#Aktenplan')

class Test_get_subject_for_selection(object):
    def setUp(self):
        _add_subject_mapping_file_to_config()
        self.result = get_subject_for_selection()
    
    def tearDown(self):
        config.clear()

    def test_it_returns_a_list(self):
        assert type(self.result) is list
    
    def test_first_element_is_empty(self):
        nt.assert_equal(self.result[0], {'key': 'empty', 'value': ' '})
    
    def test_it_contains_more_than_one_element(self):
        nt.assert_greater(len(self.result), 1)

        
