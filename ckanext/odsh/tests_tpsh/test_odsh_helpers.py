import datetime
import nose.tools as nt
from mock import patch

import ckan.lib.helpers as helpers

import ckanext.odsh.helpers as odsh_helpers
from ckanext.odsh.helpers import is_within_last_month
import ckanext.odsh.collection.helpers as helpers_collection
import ckan.model as model


class Test_tpsh_get_successor_and_predecessor_dataset(object):
    
    def setUp(self):
        
        # construct datasets that shall be in following order:
        # name      date
        # public2   2014-07-01
        # public3   2014-07-01
        # public4   2014-07-02
        # public1   2014-07-03

        self.names_collection_members = [
            u'public3', u'public2', u'public1', u'public4', 
            u'private3', u'private2', u'private1']
        self.dates_collection_members = [
            u'2014-07-01T00:00:00', #public3
            u'2014-07-01T00:00:00', #public2
            u'2014-07-03T00:00:00', #public1
            u'2014-07-02T00:00:00', #public4
            u'2014-07-05T00:00:00', #private3
            u'2014-07-06T00:00:00', #private2
            u'2014-07-07T00:00:00', #private1
        ]
        self.pkg_dicts_collection_members = [
            {
                u'name': name,
                u'extras': {u'issued': date}
            }
            for (name, date) in zip(self.names_collection_members, self.dates_collection_members)
        ]

        def fake_access_checker(access_type, pkg_dict):
            pkg_name = pkg_dict.get('name')
            if 'public' in pkg_name:
                return True
            return False
        
        def fake_get_package_dict(name):
            package_list = filter(lambda pkg_dict:pkg_dict.get('name')==name, self.pkg_dicts_collection_members)
            return package_list[0]

        self.patch_get_datasets_belonging_to_collection_by_dataset = patch.object(
            helpers_collection,
            'get_all_datasets_belonging_to_collection_by_dataset',
            return_value = self.names_collection_members)
        self.patch_get_datasets_belonging_to_collection_by_dataset.start()

        self.patch_check_access = patch.object(
            helpers,
            'check_access',
            new=fake_access_checker, 
        )
        self.patch_check_access.start()

        self.patch_get_package_dict = patch.object(
            helpers_collection,
            'get_package_dict',
            new=fake_get_package_dict,
        )
        self.patch_get_package_dict.start()
    
    def tearDown(self):
        self.patch_get_datasets_belonging_to_collection_by_dataset.stop()
        self.patch_check_access.stop()
        self.patch_get_package_dict.stop()

    def test_patch_get_datasets_belonging_to_collection_by_dataset(self):
        return_value = helpers_collection.get_all_datasets_belonging_to_collection_by_dataset()
        nt.assert_equal(return_value, self.names_collection_members)
    
    def test_patch_access_checker_returns_True(self):
        pkg_dict = {u'name': u'public1'}
        has_access = helpers.check_access('package_show', pkg_dict)
        nt.assert_true(has_access)
    
    def test_patch_access_checker_returns_False(self):
        pkg_dict = {u'name': u'private1'}
        has_access = helpers.check_access('package_show', pkg_dict)
        nt.assert_false(has_access)
    
    def test_patch_package_get(self):
        pkg_dict = helpers_collection.get_package_dict('public1')
        nt.assert_equal(pkg_dict.get('name'), 'public1')
    
    def test_it_returns_correct_for_public2(self):
        pkg_dict = {u'name': u'public2'}
        successor, predecessor = helpers_collection.get_successor_and_predecessor_dataset(pkg_dict)
        nt.assert_equal(successor, 'public3')
        nt.assert_equal(predecessor, None)
    
    def test_it_returns_correct_for_public3(self):
        pkg_dict = {u'name': u'public3'}
        successor, predecessor = helpers_collection.get_successor_and_predecessor_dataset(pkg_dict)
        nt.assert_equal(successor, 'public4')
        nt.assert_equal(predecessor, 'public2')

    def test_it_returns_correct_for_public4(self):
        pkg_dict = {u'name': u'public4'}
        successor, predecessor = helpers_collection.get_successor_and_predecessor_dataset(pkg_dict)
        nt.assert_equal(successor, 'public1')
        nt.assert_equal(predecessor, 'public3')

    def test_it_returns_correct_for_public1(self):
        pkg_dict = {u'name': u'public1'}
        successor, predecessor = helpers_collection.get_successor_and_predecessor_dataset(pkg_dict)
        nt.assert_equal(successor, None)
        nt.assert_equal(predecessor, 'public4')
    
    def test_it_returns_None_if_no_siblings(self):
        with patch.object(
            helpers_collection,
            'get_all_datasets_belonging_to_collection_by_dataset',
            return_value = list()
        ):
            pkg_dict = {u'name': u'some_name'}
            successor, predecessor = helpers_collection.get_successor_and_predecessor_dataset(pkg_dict)
            nt.assert_equal(successor, None)
            nt.assert_equal(predecessor, None)


class Test_is_within_last_month(object):
    def test_it_returns_true_for_simple_query(self):
        date = datetime.date(2019, 4, 15)
        date_ref = datetime.date(2019, 4, 29)
        assert is_within_last_month(date, date_ref)
    
    def test_it_uses_today_if_date_ref_missing(self):
        date = datetime.date.today() - datetime.timedelta(days=20)
        assert is_within_last_month(date)
    
    def test_it_returns_true_for_dates_in_different_years(self):
        date = datetime.date(2018, 12, 16)
        date_ref = datetime.date(2019, 1, 15)
        assert is_within_last_month(date, date_ref)
    
    def test_it_returns_false_for_dates_in_different_years(self):
        date = datetime.date(2018, 12, 15)
        date_ref = datetime.date(2019, 1, 15)
        assert is_within_last_month(date, date_ref)==False
    
    def test_it_returns_true_for_dates_in_differen_months(self):
        date = datetime.date(2018, 6, 16)
        date_ref = datetime.date(2018, 7, 10)
        assert is_within_last_month(date, date_ref)
    
    def test_it_return_false_for_date_in_different_months(self):
        date = datetime.date(2018, 6, 8)
        date_ref = datetime.date(2018, 7, 10)
        assert is_within_last_month(date, date_ref)==False