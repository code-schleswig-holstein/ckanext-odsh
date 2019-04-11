import sys
import json
from nose.tools import *
from mock import MagicMock, Mock, patch


def mockInvalid(*args, **kwargs):
    return Exception(*args, **kwargs)

def mock_(s):
    return s

m = MagicMock()
class MissingMock:
    pass
m.Missing=MissingMock

sys.modules['ckan'] = MagicMock()
sys.modules['ckan.plugins'] = MagicMock()
sys.modules['ckan.plugins.toolkit'] = MagicMock()
sys.modules['ckan.model'] = MagicMock()
sys.modules['ckan.lib'] = MagicMock()
sys.modules['ckan.lib.navl'] = MagicMock()
sys.modules['ckan.lib.navl.dictization_functions'] = m
sys.modules['pylons'] = MagicMock()

import ckan.model as modelMock
import pylons
import ckan.plugins.toolkit as toolkit

toolkit.Invalid = mockInvalid
toolkit._ = mock_


from ckanext.odsh.validation import *


def test_get_validators():
    assert get_validators()


def test_tag_string_convert():
    # arrange
    data = {'tag_string': 'tag1,tag2'}
    # act
    tag_string_convert('tag_string', data, {}, None)
    # assert
    assert data[('tags', 0, 'name')] == 'tag1'
    assert data[('tags', 1, 'name')] == 'tag2'


@raises(Exception)
def test_tag_name_validator_invalid():
    tag_name_validator('&', None)


def test_tag_name_validator_valid():
    tag_name_validator('valid', None)


@patch('urllib2.urlopen')
@patch('pylons.config.get', side_effect='foo')
@patch('csv.reader', side_effect=[[['uri', 'text', json.dumps({"geometry": 0})]]])
def test_known_spatial_uri(url_mock, get_mock, csv_mock):
    # arrange
    data = {('extras', 0, 'key'): 'spatial_uri',
            ('extras', 0, 'value'): 'uri'}
    # act
    known_spatial_uri('spatial_uri', data, {}, None)
    # assert
    assert data[('extras', 1, 'key')] == 'spatial_text'
    assert data[('extras', 1, 'value')] == 'text'
    assert data[('extras', 2, 'key')] == 'spatial'
    assert data[('extras', 2, 'value')] == '0'


def test_validate_licenseAttributionByText():
    # arrange
    def get_licenses():
        return {}
    modelMock.Package.get_license_register = get_licenses
    data = {'license_id': '0',
            ('extras', 0, 'key'): 'licenseAttributionByText',
            ('extras', 0, 'value'): ''}
    validate_licenseAttributionByText('key', data, {}, None)
