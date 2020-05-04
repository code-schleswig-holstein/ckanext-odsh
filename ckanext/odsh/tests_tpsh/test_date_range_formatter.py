 # -*- coding: utf-8 -*-

import nose.tools as nt

import datetime

from ckanext.odsh.pretty_daterange.date_range_formatter import DateRangeFormatter

class TestDateRangeFormatter(object):
    def test_it_raises_value_error_if_date_end_before_date_start(self):
        date_start = datetime.date(2019,1,1)
        date_end = datetime.date(2018,1,1)
        with nt.assert_raises(ValueError):
            drf = DateRangeFormatter(date_start, date_end)
    
    def test_it_stores_date_start_and_date_end(self):
        date_start = datetime.date(2019,1,1)
        date_end = datetime.date(2019,2,1)
        drf = DateRangeFormatter(date_start, date_end)
        assert drf.date_start==date_start and drf.date_end==date_end
    
    def test_it_returns_date_in_correct_format(self):
        self._assert_output_string_equals(
            date_start = datetime.date(2019,1,2), 
            date_end = datetime.date(2020, 2, 4), 
            expected_str = u'02.01.2019 - 04.02.2020')
    
    def _assert_output_string_equals(self, date_start, date_end, expected_str):
        drf = DateRangeFormatter(date_start, date_end)
        formatted_date_range = drf.get_formatted_str()
        nt.assert_equal(formatted_date_range, expected_str)
    
    def test_it_returns_single_date_if_start_equals_end(self):
        self._assert_output_string_equals(
            date_start = datetime.date(2019, 1, 2), 
            date_end = datetime.date(2019, 1, 2), 
            expected_str = u'02.01.2019')

    def test_it_returns_only_year_for_full_year(self):
        self._assert_output_string_equals(
            date_start = datetime.date(2019, 1, 1), 
            date_end = datetime.date(2019, 12, 31), 
            expected_str = u'2019')
    
    def test_it_returns_only_year_for_multiple_full_years(self):
        self._assert_output_string_equals(
            date_start = datetime.date(2019, 1, 1), 
            date_end = datetime.date(2020, 12, 31), 
            expected_str = u'2019 - 2020')
    
    def test_it_returns_month_for_full_month(self):
        self._assert_output_string_equals(
            date_start = datetime.date(2019, 2, 1), 
            date_end = datetime.date(2019, 2, 28), 
            expected_str = u'Februar 2019')
    
    def test_it_returns_months_for_range_of_months(self):
        self._assert_output_string_equals(
            date_start = datetime.date(2019, 2, 1), 
            date_end = datetime.date(2020, 3, 31), 
            expected_str = u'Februar 2019 - März 2020')
    
    def test_it_returns_months_for_range_of_months_in_same_year(self):
        self._assert_output_string_equals(
            date_start = datetime.date(2019, 2, 1), 
            date_end = datetime.date(2019, 3, 31), 
            expected_str = u'Februar - März 2019')
    
    def test_it_returns_first_quarter(self):
        self._assert_output_string_equals(
            date_start = datetime.date(2019, 1, 1), 
            date_end = datetime.date(2019, 3, 31), 
            expected_str = u'1. Quartal 2019')
    
    def test_it_returns_second_quarter(self):
        self._assert_output_string_equals(
            date_start = datetime.date(2019, 4, 1), 
            date_end = datetime.date(2019, 6, 30), 
            expected_str = u'2. Quartal 2019')
    
    def test_it_returns_third_quarter(self):
        self._assert_output_string_equals(
            date_start = datetime.date(2019, 7, 1), 
            date_end = datetime.date(2019, 9, 30), 
            expected_str = u'3. Quartal 2019')
    
    def test_it_returns_fourth_quarter(self):
        self._assert_output_string_equals(
            date_start = datetime.date(2019, 10, 1), 
            date_end = datetime.date(2019, 12, 31), 
            expected_str = u'4. Quartal 2019')
    
    def test_it_returns_first_half_year(self):
        self._assert_output_string_equals(
            date_start = datetime.date(2019, 1, 1), 
            date_end = datetime.date(2019, 6, 30), 
            expected_str = u'1. Halbjahr 2019')

    def test_it_returns_second_half_year(self):
        self._assert_output_string_equals(
            date_start = datetime.date(2019, 7, 1), 
            date_end = datetime.date(2019, 12, 31), 
            expected_str = u'2. Halbjahr 2019')
    
    def test_it_returns_date_start_if_date_end_is_none(self):
        self._assert_output_string_equals(
            date_start = datetime.date(2019, 7, 1), 
            date_end = None, 
            expected_str = u'ab 01.07.2019'
        )
    
    def test_it_returns_date_end_if_date_start_is_none(self):
        self._assert_output_string_equals(
            date_start = None, 
            date_end = datetime.date(2019, 7, 1), 
            expected_str = u'bis 01.07.2019'
        )

    def test_it_returns_empty_string_if_date_start_and_end_are_none(self):
        self._assert_output_string_equals(
            date_start = None, 
            date_end = None, 
            expected_str = u''
        )

    def test_it_returns_date_start_if_date_end_is_empty(self):
        self._assert_output_string_equals(
            date_start = datetime.date(2019, 7, 1), 
            date_end = '', 
            expected_str = u'ab 01.07.2019'
        )
    
    def test_it_returns_date_end_if_date_start_is_empty(self):
        self._assert_output_string_equals(
            date_start = '', 
            date_end = datetime.date(2019, 7, 1), 
            expected_str = u'bis 01.07.2019'
        )

    def test_it_returns_empty_string_if_date_start_and_end_are_empty(self):
        self._assert_output_string_equals(
            date_start = '', 
            date_end = '', 
            expected_str = u''
        )