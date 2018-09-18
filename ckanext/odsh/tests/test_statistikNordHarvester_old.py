#!/usr/bin/env python
from unittest import TestCase

import ckanext
from mock import patch

#from ckanext.harvest.model import HarvestObject
from ckanext.odsh.harvesters.statistiknordharvester import StatistikNordHarvester as harvester
from ckan import model


class HarvestObject():
    def __init__(self, content):
        self.Content = content


class TestStatistikNordHarvester(TestCase):

    harvest_object = HarvestObject



    @patch('ckanext.odsh.harvesters.statistiknordharvester.get_action')

    def test_map_fields(mock_map_fields,*args):
        mock_map_fields.return_value = ""

        content = {}
        h1 = HarvestObject(content)
        context = {
            'model': model,
            'session': model.Session,
            'user': unicode('default'),
        }

        result = harvester.map_fields(snh, context, h1)

        assert result == ""




    def map_to_group(self):

        self.fail()

