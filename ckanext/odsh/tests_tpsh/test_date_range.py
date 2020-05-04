 # -*- coding: utf-8 -*-

import nose.tools as nt

import datetime

from ckanext.odsh.pretty_daterange.date_range import DateRange

class TestDateRange(object):
    def test_is_one_year_returns_true(self):
        dr = DateRange(
            date_start = datetime.date(2000, 1, 1),
            date_end = datetime.date(2000, 12, 31)
        )
        assert dr.is_one_year()
    
    def test_is_one_year_returns_false_for_less_than_one_year(self):
        dr = DateRange(
            date_start = datetime.date(2000, 1, 1),
            date_end = datetime.date(2000, 12, 30)
        )
        assert dr.is_one_year()==False
    
    def test_is_one_year_returns_false_for_more_than_one_year(self):
        dr = DateRange(
            date_start = datetime.date(2000, 1, 1),
            date_end = datetime.date(2001, 1, 15)
        )
        assert dr.is_one_year()==False
    
    def test_is_one_year_returns_false_for_two_years(self):
        dr = DateRange(
            date_start = datetime.date(2000, 1, 1),
            date_end = datetime.date(2001, 12, 31)
        )
        assert dr.is_one_year()==False
    
    def test_is_one_half_of_year_returns_true_for_first_half(self):
        dr = DateRange(
            date_start = datetime.date(2000, 1, 1),
            date_end = datetime.date(2000, 6, 30)
        )
        assert dr.is_one_half_of_year()
    
    def test_is_one_half_of_year_returns_true_for_second_half(self):
        dr = DateRange(
            date_start = datetime.date(2000, 7, 1),
            date_end = datetime.date(2000, 12, 31)
        )
        assert dr.is_one_half_of_year()
    
    def test_is_one_half_of_year_returns_false_for_full_year(self):
        dr = DateRange(
            date_start = datetime.date(2000, 1, 1),
            date_end = datetime.date(2000, 12, 31)
        )
        assert dr.is_one_half_of_year()==False
    
    def test_get_half_year_returns_1_for_first_half_of_year(self):
        half_year = DateRange.get_half_year(datetime.date(2000, 6, 30))
        nt.assert_equal(half_year, 1)
    
    def test_get_half_year_returns_2_for_second_half_of_year(self):
        half_year = DateRange.get_half_year(datetime.date(2000, 7, 1))
        nt.assert_equal(half_year, 2)
    
    def test_is_one_quarter_of_year_returns_true_for_first_quarter(self):
        dr = DateRange(
            date_start = datetime.date(2000, 1, 1),
            date_end = datetime.date(2000, 3, 31)
        )
        assert dr.is_one_quarter_of_year()
    
    def test_is_one_quarter_of_year_returns_true_for_second_quarter(self):
        dr = DateRange(
            date_start = datetime.date(2000, 4, 1),
            date_end = datetime.date(2000, 6, 30)
        )
        assert dr.is_one_quarter_of_year()

    def test_is_one_quarter_of_year_returns_true_for_third_quarter(self):
        dr = DateRange(
            date_start = datetime.date(2000, 7, 1),
            date_end = datetime.date(2000, 9, 30)
        )
        assert dr.is_one_quarter_of_year()
    
    def test_is_one_quarter_of_year_returns_true_for_fourth_quarter(self):
        dr = DateRange(
            date_start = datetime.date(2000, 10, 1),
            date_end = datetime.date(2000, 12, 31)
        )
        assert dr.is_one_quarter_of_year()
    
    def test_get_quarter_returns_1_for_first_quarter(self):
        quarter = DateRange.get_quarter(datetime.date(2000, 2, 1))
        nt.assert_equal(quarter, 1)
    
    def test_get_quarter_returns_2_for_second_quarter(self):
        quarter = DateRange.get_quarter(datetime.date(2000, 5, 1))
        nt.assert_equal(quarter, 2)

    def test_get_quarter_returns_3_for_third_quarter(self):
        quarter = DateRange.get_quarter(datetime.date(2000, 8, 1))
        nt.assert_equal(quarter, 3)
    
    def test_get_quarter_returns_4_for_fourth_quarter(self):
        quarter = DateRange.get_quarter(datetime.date(1981, 11, 21))
        nt.assert_equal(quarter, 4)

    def test_is_one_month_returns_true(self):
        dr = DateRange(
            date_start = datetime.date(2000, 12, 1),
            date_end = datetime.date(2000, 12, 31)
        )
        assert dr.is_one_month()

    def test_is_one_month_returns_false_for_two_months(self):
        dr = DateRange(
            date_start = datetime.date(2000, 11, 1),
            date_end = datetime.date(2000, 12, 31)
        )
        assert dr.is_one_month()==False
    
    def test_is_range_of_multiple_months_returns_false_for_single_month(self):
        dr = DateRange(
            date_start = datetime.date(2000, 11, 1),
            date_end = datetime.date(2000, 11, 30)
        )
        assert dr.is_range_of_multiple_months()==False
    
    def test_is_range_of_multiple_months_returns_true_for_multiple_months(self):
        dr = DateRange(
            date_start = datetime.date(2000, 11, 1),
            date_end = datetime.date(2021, 12, 31)
        )
        assert dr.is_range_of_multiple_months()
    
    def test_is_range_of_multiple_months_in_same_year_returns_false_for_differing_years(self):
        dr = DateRange(
            date_start = datetime.date(2000, 11, 1),
            date_end = datetime.date(2021, 12, 31)
        )
        assert dr.is_range_of_multiple_months_in_same_year()==False

    def test_is_range_of_multiple_months_in_same_year_returns_true_for_same_year(self):
        dr = DateRange(
            date_start = datetime.date(2000, 11, 1),
            date_end = datetime.date(2000, 12, 31)
        )
        assert dr.is_range_of_multiple_months_in_same_year()

    def test_is_range_of_multiple_years_returns_false_for_single_year(self):
        dr = DateRange(
            date_start = datetime.date(2000, 1, 1),
            date_end = datetime.date(2000, 12, 31)
        )
        assert dr.is_range_of_multiple_years() == False