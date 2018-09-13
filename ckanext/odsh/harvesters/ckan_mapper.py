#!/usr/bin/env python
"""
Mapper, that loads all necessary mapping files, calls the pyjq method and returns the value.
"""
import json
import pyjq as pyjq

# import the "stat_amt_nord" configuration file to determine
# 1st the mapping from statistikamt nord fields onto ckan-fields and
# 2nd the mapping form the category numbers onto the MDR data-theme authority codes
import config_stat_amt_nord as sta_amt_nord


def pyjq_mapper(config_filter, value, numbers):
    # print "value: " + str(value)
    tmp = pyjq.all(config_filter, value, vars={"numbers": numbers})

    # print "tmp cm: " + str(tmp)
    return dict(tmp[0])


# for very little testing reasons regarding the pyjq lib only
test_config_filter = sta_amt_nord.config_filter
test_numbers = sta_amt_nord.numbers

with open('/usr/lib/ckan/default/src/ckanext-odsh/ckanext/odsh/harvesters/statistik-nord-example_2.json') as f:
    input = json.load(f)
    print "Input: " + str(input)
    result = dict(pyjq_mapper(test_config_filter, input, test_numbers))
print "Result: " + str(result)

