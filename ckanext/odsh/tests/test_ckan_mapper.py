#!/usr/bin/env python
import json
import unittest

from ckanext.odsh.harvesters import ckan_mapper as mapper


def value_error():
    raise ValueError('Config string can not be empty.')

class TestMappingMethodsStatistikamtNord(unittest.TestCase):

    # Files to load
    with open('/usr/lib/ckan/default/src/ckanext-odsh/ckanext/odsh/tests/test_data.json') as f:
        input_data = json.load(f)
    with open('/usr/lib/ckan/default/src/ckanext-odsh/ckanext/odsh/tests/result_data.json') as f:
        expected_result = json.load(f)

    # Loads statistikamt nord specific configurations
    config_filter = mapper.sta_amt_nord.config_filter
    numbers = mapper.sta_amt_nord.numbers


    # Test pyjq mapper with invalid StANKategorie
    def test_pyjq_mapper_with_invalid_config_string(self):

        # Save the data for generating new input for the test
        test_dict = self.input_data

        # Arrange
        self.config_filter = ""
        # Act

        # Assert
        with self.assertRaises(ValueError):
            mapper.pyjq_mapper(self.config_filter, test_dict, self.numbers)
            value_error



    # Test pyjq mapper with invalid StANKategorie
    def test_pyjq_mapper_with_invalid_StANKategorie(self):

        # Save the data for generating new input for the test
        test_dict = self.input_data

        # Arrange
        # Set category to a value, that can not be mapped
        test_dict["StANKategorie"] = unicode(0)
        # Set the expected result data correctly
        self.expected_result["groups"] = []

        # Act
        package = mapper.pyjq_mapper(self.config_filter, test_dict, self.numbers)

        # Assert
        self.assertEqual(package, self.expected_result)


if __name__ == '__main__':
    unittest.main()
