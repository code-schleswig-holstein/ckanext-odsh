# encoding: utf-8

import ckan.tests.factories as factories
import ckan.tests.helpers as helpers
from bs4 import BeautifulSoup
from ckan import model
from ckan.lib.mailer import create_reset_key
from nose.tools import assert_true, assert_false, assert_equal, assert_in
from routes import url_for
import ckan.plugins


def odsh_test(): return helpers.change_config('ckanext.odsh.spatial.mapping',
                                              'file:///usr/lib/ckan/default/src/ckanext-odsh/ckanext/odsh/tests/spatial_mapping.csv')


class TestSearch(helpers.FunctionalTestBase):

    _load_plugins = ['odsh', 'spatial_metadata', 'spatial_query']

    def teardown(self):
        model.repo.rebuild_db()

    @odsh_test()
    def test_dataset_is_in_search_result(self):
        # arrange
        dataset = self._create_dataset()

        # act
        response = self._perform_search()

        # assert
        assert dataset['name'] in response

    @odsh_test()
    def test_query_with_no_match_finds_no_dataset(self):
        # arrange
        dataset = self._create_dataset()

        # act
        response = self._perform_search("foobar")

        # assert
        self._assert_no_results(response)

    @odsh_test()
    def test_query_with_no_dates_finds_dataset(self):
        # arrange
        dataset = self._create_dataset()

        # act
        response = self._perform_date_search(None, None)

        # assert
        assert dataset['name'] in response

    @odsh_test()
    def test_query_with_start_date_finds_one_dataset(self):
        # arrange
        datasetA = self._create_dataset('dataseta', '01-01-1960', '31-12-1960')
        datasetB = self._create_dataset('datasetb', '01-01-1980', '30-06-1990')
        datasetC = self._create_dataset('datasetc', '01-03-2001', '30-04-2001')

        # act
        response1 = self._perform_date_search(None, '1990-01-01')
        response2 = self._perform_date_search(None, '2010-12-31')
        response3 = self._perform_date_search('2010-12-31', None)
        response4 = self._perform_date_search('1985-04-01', '1985-04-20')
        response5 = self._perform_date_search('2001-04-01', None)

        # assert
        self._assert_datasets_in_response([datasetA, datasetB], response1)
        self._assert_datasets_not_in_response([datasetC], response1)

        self._assert_datasets_in_response(
            [datasetA, datasetB, datasetC], response2)

        self._assert_no_results(response3)

        self._assert_datasets_in_response([datasetB], response4)
        self._assert_datasets_not_in_response([datasetA, datasetC], response4)

        self._assert_datasets_in_response([datasetC], response5)
        self._assert_datasets_not_in_response([datasetA, datasetB], response5)

    def _assert_datasets_in_response(self, datasets, response):
        for dataset in datasets:
            assert dataset['name'] in response

    def _assert_datasets_not_in_response(self, datasets, response):
        for dataset in datasets:
            assert dataset['name'] not in response

    def _assert_no_results(self, response):
        assert "No datasets found" in response

    def _create_dataset(self, name='my-own-dataset', temporal_start='27-01-2000', temporal_end='27-01-2000'):
        user = factories.User()
        return factories.Dataset(user=user,
                                 name=name,
                                 title='My very own dataset',
                                 issued='27-01-2000',
                                 spatial_uri='http://dcat-ap.de/def/politicalGeocoding/districtKey/01001',
                                 temporal_start=temporal_start,
                                 temporal_end=temporal_end)

    def _perform_search(self, query=None):
        search_form = self._perform_search_for_form('dataset-search-box-form')
        if query is not None:
            search_form['q'] = query
        return helpers.webtest_submit(search_form)

    def _perform_date_search(self, search_from, search_to):
        search_form = self._perform_search_for_form('date-search-form')
        if search_form is not None:
            search_form['ext_startdate'] = search_from
        if search_to is not None:
            search_form['ext_enddate'] = search_to
        return helpers.webtest_submit(search_form)

    def _perform_search_for_form(self, form):
        search_url = url_for(controller='package', action='search')
        search_response = self._get_test_app().get(search_url)

        search_form = search_response.forms[form]
        return search_form
