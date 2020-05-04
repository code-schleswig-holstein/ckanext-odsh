import nose.tools as nt
import ckanext.odsh.search as search

class Test_before_search(object):
    def setUp(self):
        self.search_params_before_test = {
            'extras': {}, 
            'facet.field': ['organization', 'subject_text', 'groups'], 
            'fq': u'organization:"test-organisation" groups:"gove" subject_text:"T\xe4tigkeitsbericht" +dataset_type:dataset', 
            'include_private': True, 
            'q': u'', 
            'rows': 20, 
            'sort': u'score desc, metadata_modified desc', 
            'start': 0
        }
        self.search_params_with_facet_mincount = self.search_params_before_test.copy()
        self.search_params_with_facet_mincount.update({'facet.mincount': 0})
    
    def test_it_solely_adds_facet_mincount_to_dict_if_no_extras(self):
        # arange
        search_params = self.search_params_before_test.copy()
        # act
        search.before_search(search_params)
        # assert
        search_params_expected = self.search_params_with_facet_mincount.copy()
        nt.assert_equal(search_params, search_params_expected)

    def test_it_adds_fq_if_empty_range(self):
        # arange
        search_params = self.search_params_before_test.copy()
        extras = {'ext_enddate': u'2019-08-01', 'ext_startdate': u'2019-08-02'}
        search_params.update({'extras': extras})
        search_params_expected = self.search_params_with_facet_mincount.copy()
        search_params_expected.update({'extras': extras})
        search_params_expected.update({
            'fq': (
                u'organization:"test-organisation" groups:"gove" subject_text:"T\xe4tigkeitsbericht" '
                u'+dataset_type:dataset (+extras_temporal_start:[2019-08-02T00:00:00Z TO 2019-08-01T00:00:00Z] '
                u'OR +extras_temporal_end:[2019-08-02T00:00:00Z TO 2019-08-01T00:00:00Z]  OR '
                u'((*:* NOT extras_temporal_end:[* TO *]) AND extras_temporal_start:[* TO 2019-08-01T00:00:00Z]))'
            )
        })
        # act
        search.before_search(search_params)
        # assert
        nt.assert_equal(search_params, search_params_expected)
    
    def test_it_solely_adds_facet_mincount_to_dict_if_wrong_date_format_in_extras(self):
        # arange
        search_params = self.search_params_before_test.copy()
        extras = {'ext_enddate': u'some_date', 'ext_startdate': u'some_date'}
        search_params.update({'extras': extras})
        search_params_expected = self.search_params_with_facet_mincount.copy()
        search_params_expected.update({'extras': extras})
        # act
        search.before_search(search_params)
        # assert
        nt.assert_equal(search_params, search_params_expected)
    
    def test_it_adds_fq_if_enclosing_range(self):
        # arange
        search_params = self.search_params_before_test.copy()
        extras = {'ext_enddate': u'2019-08-02', 'ext_startdate': u'2019-08-01'}
        search_params.update({'extras': extras})
        search_params_expected = self.search_params_with_facet_mincount.copy()
        search_params_expected.update({'extras': extras})
        search_params_expected.update({
            'fq': (
                u'organization:"test-organisation" groups:"gove" '
                u'subject_text:"T\xe4tigkeitsbericht" +dataset_type:dataset '
                u'(+extras_temporal_start:[2019-08-01T00:00:00Z TO 2019-08-02T00:00:00Z] '
                u'OR +extras_temporal_end:[2019-08-01T00:00:00Z TO 2019-08-02T00:00:00Z]  '
                u'OR (extras_temporal_start:[* TO 2019-08-01T00:00:00Z] AND '
                u'extras_temporal_end:[2019-08-02T00:00:00Z TO *]) OR '
                u'((*:* NOT extras_temporal_end:[* TO *]) AND '
                u'extras_temporal_start:[* TO 2019-08-02T00:00:00Z]))'
            )
        })
        # act
        search.before_search(search_params)
        # assert
        nt.assert_equal(search_params, search_params_expected)

    def test_it_adds_fq_if_start_only(self):
        # arange
        search_params = self.search_params_before_test.copy()
        extras = {'ext_startdate': u'2019-08-01'}
        search_params.update({'extras': extras})
        search_params_expected = self.search_params_with_facet_mincount.copy()
        search_params_expected.update({'extras': extras})
        search_params_expected.update({
            'fq': (
                u'organization:"test-organisation" groups:"gove" '
                u'subject_text:"T\xe4tigkeitsbericht" +dataset_type:dataset '
                u'(+extras_temporal_start:[2019-08-01T00:00:00Z TO *] '
                u'OR +extras_temporal_end:[2019-08-01T00:00:00Z TO *]  '
                u'OR (*:* NOT extras_temporal_end:[* TO *]))'
            )
        })
        # act
        search.before_search(search_params)
        # assert
        nt.assert_equal(search_params, search_params_expected)
    
    def test_it_adds_fq_if_end_only(self):
        # arange
        search_params = self.search_params_before_test.copy()
        extras = {'ext_enddate': u'2019-08-02'}
        search_params.update({'extras': extras})
        search_params_expected = self.search_params_with_facet_mincount.copy()
        search_params_expected.update({'extras': extras})
        search_params_expected.update({
            'fq': (
                u'organization:"test-organisation" groups:"gove" '
                u'subject_text:"T\xe4tigkeitsbericht" +dataset_type:dataset '
                u'(+extras_temporal_start:[* TO 2019-08-02T00:00:00Z] OR '
                u'+extras_temporal_end:[* TO 2019-08-02T00:00:00Z]  '
                u'OR ((*:* NOT extras_temporal_end:[* TO *]) '
                u'AND extras_temporal_start:[* TO 2019-08-02T00:00:00Z]))'
            )
        })
        # act
        search.before_search(search_params)
        # assert
        nt.assert_equal(search_params, search_params_expected)
    
    def test_it_returns_search_params(self):
        # arange
        search_params = self.search_params_before_test.copy()
        # act
        return_value = search.before_search(search_params)
        # assert
        nt.assert_equal(return_value, search_params)
