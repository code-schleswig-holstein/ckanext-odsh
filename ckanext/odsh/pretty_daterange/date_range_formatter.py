 # -*- coding: utf-8 -*-

import datetime
from babel.dates import format_date

from .date_range import DateRange

class DateRangeFormatter(object):
    def __init__(self, date_start, date_end):
        if all((date_start, date_end)):
            self._date_range = DateRange(date_start, date_end)
        self.locale_for_date_strings = 'de_DE.UTF-8'
        self.date_start = date_start
        self.date_end = date_end
        self._format_full_date = 'dd.MM.yyyy'
        self._format_only_year = 'yyyy'
        self._format_month_year = 'MMMM yyyy'
        self._format_only_month = 'MMMM'
    
    
    def get_formatted_str(self):
        if not any((self.date_start, self.date_end, )):
            return self._construct_empty_date_string()
        
        if not self.date_end:
            return self._construct_open_end_date_string()
        
        if not self.date_start:
            return self._construct_open_start_date_string()
        
        if self.date_start == self.date_end:
            return self._construct_single_date_string(self.date_start, self._format_full_date)
        
        if self._date_range.is_range_of_multiple_years():
            return self._construct_date_range_string(self._format_only_year, self._format_only_year)
        
        if self._date_range.is_one_year():
            return self._construct_single_date_string(self.date_start, self._format_only_year)
        
        if self._date_range.is_one_half_of_year():
            return self._construct_half_of_year_date_string()
        
        if self._date_range.is_one_quarter_of_year():
            return self._construct_quarter_of_year_date_string()

        if self._date_range.is_range_of_multiple_months_in_same_year():
            return self._construct_date_range_string(self._format_only_month, self._format_month_year)
        
        if self._date_range.is_range_of_multiple_months():
            return self._construct_date_range_string(self._format_month_year, self._format_month_year)

        if self._date_range.is_one_month():
            return self._construct_single_date_string(self.date_start, self._format_month_year)
        
        format_date_start = self._format_full_date
        format_date_end = self._format_full_date
        formatted_date_range = self._construct_date_range_string(format_date_start, format_date_end)
        return formatted_date_range
    
    
    @staticmethod
    def _construct_empty_date_string():
        return ""
    
    def _construct_open_end_date_string(self):
        date_start_formatted = self._construct_single_date_string(self.date_start, self._format_full_date)
        return "ab {}".format(date_start_formatted)
    
    def _construct_open_start_date_string(self):
        date_end_formatted = self._construct_single_date_string(self.date_end, self._format_full_date)
        return "bis {}".format(date_end_formatted)
    
    def _construct_single_date_string(self, date, format):
        return format_date(date, format=format, locale=self.locale_for_date_strings)

    @staticmethod
    def _as_utf_8(s):
        return u'' + s.decode('utf-8')
    
    
    def _construct_half_of_year_date_string(self):
        year = self.date_start.year
        half = self._date_range.get_half_year(self.date_start)
        half_of_year_date_string = u'{}. Halbjahr {}'.format(half, year)
        return DateRangeFormatter._as_utf_8(half_of_year_date_string)
    
    
    def _construct_quarter_of_year_date_string(self):
        year = self.date_start.year
        quarter = self._date_range.get_quarter(self.date_start)
        quarter_of_year_date_string = u'{}. Quartal {}'.format(quarter, year)
        return DateRangeFormatter._as_utf_8(quarter_of_year_date_string)

    
    def _construct_date_range_string(self, format_date_start, format_date_end):
        formatted_date_range = u'{} - {}'.format(
            self._construct_single_date_string(self.date_start, format_date_start), 
            self._construct_single_date_string(self.date_end, format_date_end))
        return formatted_date_range
