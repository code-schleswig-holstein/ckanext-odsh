import datetime
import nose.tools as nt
from mock import patch, call

from ckanext.odsh.helper_pkg_dict import HelperPgkDict
import ckanext.odsh.helpers_tpsh as helpers_tpsh
import ckanext.odsh.uri_store as uri_store

class TestHelperPkgDict(object):
    def test_is_collection_returns_true(self):
        dataset_dict = {
            u'type': u'collection',
        }
        h = HelperPgkDict(dataset_dict)
        is_collection = h.is_collection()
        nt.assert_true(is_collection)
    
    def test_is_collection_returns_false_if_no_type(self):
        dataset_dict = {}
        h = HelperPgkDict(dataset_dict)
        is_collection = h.is_collection()
        nt.assert_false(is_collection)
    
    def test_is_collection_returns_false_if_type_dataset(self):
        dataset_dict = {u'type': u'dataset'}
        h = HelperPgkDict(dataset_dict)
        is_collection = h.is_collection()
        nt.assert_false(is_collection)
    
    def test_shall_be_part_of_collection_returns_true_if_flag_add_to_collection_is_True(self):
        dataset_dict = {'add_to_collection': True}
        h = HelperPgkDict(dataset_dict)
        shall_be_part_of_collection = h.shall_be_part_of_collection()
        nt.assert_true(shall_be_part_of_collection)
    
    def test_shall_be_part_of_collection_returns_false_if_flag_add_to_collection_is_False(self):
        dataset_dict = {'add_to_collection': False}
        h = HelperPgkDict(dataset_dict)
        shall_be_part_of_collection = h.shall_be_part_of_collection()
        nt.assert_false(shall_be_part_of_collection)
    
    def test_shall_be_part_of_collection_returns_false_if_flag_add_to_collection_not_in_dict(self):
        dataset_dict = {}
        h = HelperPgkDict(dataset_dict)
        shall_be_part_of_collection = h.shall_be_part_of_collection()
        nt.assert_false(shall_be_part_of_collection)
    
    def test_update_relations_to_collection_members_leads_to_correct_call_of_add_to_collection(self):
        with patch.object(helpers_tpsh, 'add_pkg_to_collection') as patch_add_package_to_collection:
            # arange
            # taken from debugging _update_relations_to_collection_members:
            dataset_dict_collection = {
                'id': u'248ceefd-2fb8-4a3c-ab3c-d2c873b24e4d',
                u'extras': [
                    {u'key': u'has_version', u'value': u'["http://transparenz.schleswig-holstein.de/9f9ae60bb0d8985e10e9ab8aa6a7ca34", "http://transparenz.schleswig-holstein.de/3a0d0674120fbf06b5cb8737124e3fd0", "http://transparenz.schleswig-holstein.de/b5cd3f303f594ecde96e1017e953b688", "http://transparenz.schleswig-holstein.de/ff612d0f165d46f3091f58e1ef56a2ec", "http://transparenz.schleswig-holstein.de/cd606b042789723a2b6d61cb31c46c39"]'},
                ]
            }
            id_collection = u'248ceefd-2fb8-4a3c-ab3c-d2c873b24e4d'
            uri_collection_member = 'http://transparenz.schleswig-holstein.de/b5cd3f303f594ecde96e1017e953b688'
            id_collection_member = 'fake_id_collection_member'
            uri_store._set_uri_to_id({uri_collection_member: id_collection_member})

            # act
            h = HelperPgkDict(dataset_dict_collection)
            h.update_relations_to_collection_members()

            # assert
            calls = [call(id_collection_member,id_collection), ]
            patch_add_package_to_collection.assert_has_calls(calls)

            # teardown
            uri_store._set_uri_to_id({})
    
    def test_update_relation_to_collection_leads_to_correct_call_of_add_to_collection(self):
        with patch.object(helpers_tpsh, 'add_pkg_to_collection') as patch_add_package_to_collection:
            # arange
            # taken from debugging _update_relations_to_collection_members:
            dataset_dict_collection_member = {
                u'add_to_collection': True,
                u'extras': [
                    {u'key': u'is_version_of', u'value': u'["http://transparenz.schleswig-holstein.de/5ffd27c528f7ab6936318da90d5cdd63"]'},
                ],
                'id': u'248ceefd-2fb8-4a3c-ab3c-d2c873b24e4d',
            }
            id_collection_member = u'248ceefd-2fb8-4a3c-ab3c-d2c873b24e4d'
            uri_collection = 'http://transparenz.schleswig-holstein.de/5ffd27c528f7ab6936318da90d5cdd63'
            id_collection = 'fake_id_collection'
            uri_store._set_uri_to_id({uri_collection: id_collection})

            # act
            h = HelperPgkDict(dataset_dict_collection_member)
            h.update_relation_to_collection()

            # assert
            calls = [call(id_collection_member,id_collection), ]
            patch_add_package_to_collection.assert_has_calls(calls)

            # teardown
            uri_store._set_uri_to_id({})
    
    def test_get_collection_uri(self):
        dataset_dict_collection_member = {
            u'add_to_collection': True,
            u'extras': [
                {u'key': u'is_version_of', u'value': u'["http://transparenz.schleswig-holstein.de/5ffd27c528f7ab6936318da90d5cdd63"]'},
            ],
            'id': u'248ceefd-2fb8-4a3c-ab3c-d2c873b24e4d',
        }
        h = HelperPgkDict(dataset_dict_collection_member)
        collection = h.get_collection_uri()
        nt.assert_equal(collection, u'http://transparenz.schleswig-holstein.de/5ffd27c528f7ab6936318da90d5cdd63')
    
    def test_get_collection_uri_if_not_in_extras(self):
        dataset_dict_collection_member = {
            u'id': u'248ceefd-2fb8-4a3c-ab3c-d2c873b24e4d',
        }
        h = HelperPgkDict(dataset_dict_collection_member)
        collection = h.get_collection_uri()
        nt.assert_equal(collection, None)
    
    def test_get_uris_collection_members(self):
        collection_members_as_string = u'["http://transparenz.schleswig-holstein.de/cd606b042789723a2b6d61cb31c46c39", "http://transparenz.schleswig-holstein.de/3a0d0674120fbf06b5cb8737124e3fd0", "http://transparenz.schleswig-holstein.de/b5cd3f303f594ecde96e1017e953b688", "http://transparenz.schleswig-holstein.de/9f9ae60bb0d8985e10e9ab8aa6a7ca34", "http://transparenz.schleswig-holstein.de/ff612d0f165d46f3091f58e1ef56a2ec"]'
        dataset_dict = {
            u'extras': [
                {u'key': u'has_version', u'value': collection_members_as_string},
            ]
        }
        h = HelperPgkDict(dataset_dict)
        uris = h.get_uris_collection_members()
        nt.assert_equal(uris[0], 'http://transparenz.schleswig-holstein.de/cd606b042789723a2b6d61cb31c46c39')
        nt.assert_equal(uris[1], 'http://transparenz.schleswig-holstein.de/3a0d0674120fbf06b5cb8737124e3fd0')
        nt.assert_equal(uris[-1], 'http://transparenz.schleswig-holstein.de/ff612d0f165d46f3091f58e1ef56a2ec')



class Test_get_date_start_and_end_from_pkg_dict(object):

    def setUp(self):
        self.dict_with_start_and_end_date = {
            u'extras': [
                {u'key': u'groups', u'value': u''}, 
                {u'key': u'issued', u'value': u'2019-07-06T00:00:00'}, 
                {u'key': u'licenseAttributionByText', u'value': u''}, 
                {u'key': u'subject_text', u'value': u''}, 
                {u'key': u'temporal_end', u'value': u'2019-08-31T00:00:00'}, 
                {u'key': u'temporal_start', u'value': u'2019-08-01T00:00:00'}
            ],
        }
        self.dict_with_empty_start_date = {
            u'extras': [
                {u'key': u'groups', u'value': u''}, 
                {u'key': u'issued', u'value': u'2019-07-06T00:00:00'}, 
                {u'key': u'licenseAttributionByText', u'value': u''}, 
                {u'key': u'subject_text', u'value': u''}, 
                {u'key': u'temporal_end', u'value': u'2019-08-31T00:00:00'}, 
                {u'key': u'temporal_start', u'value': u''}
            ],
        }
        self.dict_with_empty_end_date = {
            u'extras': [
                {u'key': u'groups', u'value': u''}, 
                {u'key': u'issued', u'value': u'2019-07-06T00:00:00'}, 
                {u'key': u'licenseAttributionByText', u'value': u''}, 
                {u'key': u'subject_text', u'value': u''}, 
                {u'key': u'temporal_end', u'value': u''}, 
                {u'key': u'temporal_start', u'value': u'2019-08-01T00:00:00'}
            ],
        }
        self.date_start_expected = datetime.date(2019, 8, 1)
        self.date_end_expected = datetime.date(2019, 8, 31)

    def test_it_returns_correct_start_date(self):
        h = HelperPgkDict(self.dict_with_start_and_end_date)
        date_start, _ = h._get_date_start_and_end_from_pkg_dict()
        nt.assert_equal(date_start, self.date_start_expected)
    
    def test_it_returns_correct_end_date(self):
        h = HelperPgkDict(self.dict_with_start_and_end_date)
        _, date_end = h._get_date_start_and_end_from_pkg_dict()
        nt.assert_equal(date_end, self.date_end_expected)
    
    def test_it_return_none_if_date_start_empty(self):
        h = HelperPgkDict(self.dict_with_empty_start_date)
        date_start, _ = h._get_date_start_and_end_from_pkg_dict()
        nt.assert_equal(date_start, None)
    
    def test_it_return_none_if_date_end_empty(self):
        h = HelperPgkDict(self.dict_with_empty_end_date)
        _, date_end = h._get_date_start_and_end_from_pkg_dict()
        nt.assert_equal(date_end, None)
    
    def test_it_returns_date_start_if_date_end_empty(self):
        h = HelperPgkDict(self.dict_with_empty_end_date)
        date_start, _ = h._get_date_start_and_end_from_pkg_dict()
        nt.assert_equal(date_start, self.date_start_expected)
    
    def test_it_returns_date_end_if_date_start_empty(self):
        h = HelperPgkDict(self.dict_with_empty_start_date)
        _, date_end = h._get_date_start_and_end_from_pkg_dict()
        nt.assert_equal(date_end, self.date_end_expected)    