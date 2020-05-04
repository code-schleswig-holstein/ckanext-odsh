 # -*- coding: utf-8 -*-

import datetime

class DateRange(object):
    def __init__(self, date_start, date_end):
        if date_end < date_start:
            raise ValueError('date_end may not be before date_start')
        self.date_start = date_start
        self.date_end = date_end
    
    
    def is_one_year(self):
        is_one_year = (
            self._are_start_and_end_in_same_year() and 
            self._is_first_of_year(self.date_start) and 
            self._is_last_of_year(self.date_end)
        )
        return is_one_year

    
    def _are_start_and_end_in_same_year(self):
        in_same_year = self.date_start.year==self.date_end.year
        return in_same_year
    
    
    @staticmethod
    def _is_first_of_year(date):
        return date.day==1 and date.month==1
    
    
    @staticmethod
    def _is_last_of_year(date):
        return date.day==31 and date.month==12

    
    def is_range_of_multiple_years(self):
        is_range_of_multiple_years = (
            not self._are_start_and_end_in_same_year() and 
            self._is_first_of_year(self.date_start) and 
            self._is_last_of_year(self.date_end)
        )
        return is_range_of_multiple_years
    
    def is_one_half_of_year(self):
        is_one_half_year = (
            self._are_start_and_end_in_same_half_year() and
            self._is_first_of_half_year(self.date_start) and
            self._is_last_of_half_year(self.date_end)
        )
        return is_one_half_year
    
    
    def _are_start_and_end_in_same_half_year(self):
        in_same_half_year = (
            self._are_start_and_end_in_same_year() and
            self.get_half_year(self.date_start) == self.get_half_year(self.date_end)
        )
        return in_same_half_year
    
    
    @staticmethod
    def get_half_year(date):
        year = date.year
        if date < datetime.date(year, 7, 1):
            return 1
        return 2
    
    
    @staticmethod
    def _is_first_of_half_year(date):
        year = date.year
        return date in (
            datetime.date(year, 1, 1),
            datetime.date(year, 7, 1),
        )
    
    
    @staticmethod
    def _is_last_of_half_year(date):
        year = date.year
        return date in (
            datetime.date(year, 6, 30),
            datetime.date(year, 12, 31),
        )
    
    
    def is_one_quarter_of_year(self):
        is_one_quarter_of_year = (
            self._are_start_and_end_in_same_quarter() and
            self._is_first_of_quarter(self.date_start) and
            self._is_last_of_quarter(self.date_end)
        )
        return is_one_quarter_of_year
    
    
    def _are_start_and_end_in_same_quarter(self):
        in_same_quarter = (
            self._are_start_and_end_in_same_year() and
            self.get_quarter(self.date_start) == self.get_quarter(self.date_end)
        )
        return in_same_quarter

    
    @staticmethod
    def get_quarter(date):
        year = date.year
        if date < datetime.date(year, 4, 1):
            return 1
        if date < datetime.date(year, 7, 1):
            return 2
        if date < datetime.date(year, 10, 1):
            return 3
        return 4
    
    
    @staticmethod
    def _is_first_of_quarter(date):
        year = date.year
        return date in (
            datetime.date(year, 1, 1),
            datetime.date(year, 4, 1),
            datetime.date(year, 7, 1),
            datetime.date(year, 10, 1),
        )
    
    
    @staticmethod
    def _is_last_of_quarter(date):
        year = date.year
        return date in (
            datetime.date(year, 3, 31),
            datetime.date(year, 6, 30),
            datetime.date(year, 9, 30),
            datetime.date(year, 12, 31),
        )
    
    
    def is_one_month(self):
        is_one_month = (
            self._are_start_and_end_in_same_year() and
            self._are_start_and_end_in_same_month() and
            self._is_first_of_month(self.date_start) and 
            self._is_last_of_month(self.date_end)
        )
        return is_one_month
    
    
    def _are_start_and_end_in_same_month(self):
        is_in_same_month = self.date_start.month == self.date_end.month
        return is_in_same_month

    
    @staticmethod
    def _is_first_of_month(date):
        return date.day==1
    
    
    @staticmethod
    def _is_last_of_month(date):
        day_after_date = date + datetime.timedelta(days=1)
        is_last_of_month = day_after_date.day==1
        return is_last_of_month
    
    def is_range_of_multiple_months(self):
        is_range_of_multiple_months = (
            self._is_first_of_month(self.date_start) and 
            self._is_last_of_month(self.date_end) and
            not self._are_start_and_end_in_same_month()
        )
        return is_range_of_multiple_months
    
    def is_range_of_multiple_months_in_same_year(self):
        is_range_of_multiple_months_in_same_year = (
            self._is_first_of_month(self.date_start) and 
            self._is_last_of_month(self.date_end) and
            not self._are_start_and_end_in_same_month() and
            self._are_start_and_end_in_same_year()
        )
        return is_range_of_multiple_months_in_same_year
    
