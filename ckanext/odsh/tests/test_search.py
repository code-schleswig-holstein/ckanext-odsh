# encoding: utf-8

import ckan.tests.factories as factories
import ckan.tests.helpers as helpers
from bs4 import BeautifulSoup
from ckan import model
from ckan.lib.mailer import create_reset_key
from nose.tools import assert_true, assert_false, assert_equal, assert_in
from routes import url_for
import ckan.plugins
from test_helpers import odsh_test



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
    def test_query_with_very_old_dataset(self):
        # arrange
        dataseta = self._create_dataset('do_not_find_me', '2011-01-01', '2013-12-31')
        datasetb = self._create_dataset('old_dataset', '1111-01-01', '1860-12-31')

        # act
        response = self._perform_date_search('1110-12-30', '1960-02-01')

        # assert
        assert 'wrong_start_date_for_search' not in response
        self._assert_datasets_in_response([datasetb], response)
        self._assert_datasets_not_in_response([dataseta], response)

    @odsh_test()
    def test_query_with_end_before_start_finds_no_dataset(self):
        # arrange
        datasetA = self._create_dataset('dataseta', '1960-01-01', '1960-12-31')

        # act
        response = self._perform_date_search('1960-12-30', '1960-02-01')

        # assert
        self._assert_no_results(response)

    @odsh_test()
    def test_query_with_wrong_dates_shows_error(self):
        # arrange
        dataset = self._create_dataset()

        # act
        response1 = self._perform_date_search('foo', None)
        response2 = self._perform_date_search(None, 'foo')
        response3 = self._perform_date_search('11-11-11', None)

        # assert
        assert 'wrong_start_date_for_search' in response1
        self._assert_datasets_in_response([dataset], response1)
        assert 'daterange: to' not in response1
        assert 'daterange: from' not in response1
        assert 'wrong_end_date_for_search' in response2
        self._assert_datasets_in_response([dataset], response2)
        assert 'daterange: to' not in response2
        assert 'daterange: from' not in response2
        assert 'wrong_start_date_for_search' in response3
        assert 'daterange: to' not in response3
        assert 'daterange: from' not in response3
        self._assert_datasets_in_response([dataset], response3)

    @odsh_test()
    def test_query_with_start_date_finds_one_dataset(self):
        # arrange
        datasetA = self._create_dataset('dataseta', '1960-01-01', '1960-12-31')
        datasetB = self._create_dataset('datasetb', '1980-01-01', '1990-06-30')
        datasetC = self._create_dataset('datasetc', '2001-03-01', '2001-04-30')

        # act
        response1 = self._perform_date_search(None, '1990-01-01')
        response2 = self._perform_date_search(None, '2010-12-31')
        response3 = self._perform_date_search('2010-12-31', None)
        response4 = self._perform_date_search('1985-04-01', '1985-04-20')
        response5 = self._perform_date_search('2001-04-01', None)

        # assert
        self._assert_datasets_in_response([datasetA, datasetB], response1)
        self._assert_datasets_not_in_response([datasetC], response1)
        assert 'daterange: to' in response1

        self._assert_datasets_in_response(
            [datasetA, datasetB, datasetC], response2)
        assert 'daterange: to' in response2

        self._assert_no_results(response3)
        assert 'daterange: from' in response3

        self._assert_datasets_in_response([datasetB], response4)
        self._assert_datasets_not_in_response([datasetA, datasetC], response4)
        assert 'daterange: to' in response4
        assert 'daterange: from' in response4

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

    def _create_dataset(self, name='my-own-dataset', temporal_start='2000-01-27', temporal_end='2000-01-27'):
        user = factories.User()
        extras = [
            {'key': 'temporal_start', 'value': temporal_start},
            {'key': 'temporal_end', 'value': temporal_end},
            {'key': 'issued', 'value': '2000-01-27'},
            {'key': 'spatial_uri', 'value': 'http://dcat-ap.de/def/politicalGeocoding/districtKey/01001'}
        ]
        return factories.Dataset(user=user,
                                 name=name,
                                 title='My very own dataset',
                                 issued='27-01-2000',
                                 extras=extras)

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
