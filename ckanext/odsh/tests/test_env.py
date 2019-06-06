from ckan.common import config
import ckan.model as model
import pdb
import json
import ckanext.odsh.profiles as profiles
import urllib2
import os
import sys
import ConfigParser
from collections import OrderedDict

# run with nosetests --ckan --nologcapture --with-pylons=<config to test> ckanext/odsh/tests/test_env.py


def checkConfig(key, expected=None, minLength=None):
    value = config.get(key, None)
    assert value, "expected '{key}' to be set".format(key=key)
    if expected:
        assert value.strip() == expected, "expected '{key}' to be '{exp}' but was '{val}'".format(
            key=key, exp=expected, val=value)
    if minLength:
        assert len(value) >= minLength
    return value


def checkConfigUrl(key, expectedKey=None, responseContains=None):
    value = checkConfig(key, expected=expectedKey)

    req = urllib2.Request(value)
    response = urllib2.urlopen(req)
    data = response.read()
    if responseContains:
        assert responseContains in data


def checkConfigFile(key, expectedKey=None, responseContains=None):
    value = checkConfig(key, expected=expectedKey)

    with open(value.replace('file://', ''), 'r') as fp:
        if responseContains:
            data = fp.read()
            assert responseContains in data


def checkConfigDir(key, expectedKey=None):
    value = checkConfig(key, expected=expectedKey)
    assert os.access(value.replace('file://', ''),
                     os.W_OK), "expected '{key}={val}' to be writeable (user was '{user}')".format(key=key,val=value, user=os.getlogin())


def checkJsonFile(key, expectedKey=None, expectedLength=None):
    value = checkConfig(key, expected=expectedKey)

    with open(value.replace('file://', '')) as json_file:
        data = json.load(json_file)
        if expectedLength:
            assert len(data) >= expectedLength


def isSlave():
    value = checkConfig('ckanext.odsh.slave')
    assert value == 'True' or value == 'False'
    return checkConfig('ckanext.odsh.slave') == 'True'


def isMaster():
    return not isSlave()


class MultiOrderedDict(OrderedDict):
    def __setitem__(self, key, value):
        if isinstance(value, list) and key in self:
            raise ValueError('found duplicate config entry: ' + key)
            self[key].extend(value)
        else:
            super(OrderedDict, self).__setitem__(key, value)


def checkConfigForDuplicates():
    path = None
    for a in sys.argv:
        if a.startswith('--with-pylons'):
            path = a.split('=')[1]
            break
    assert path, 'could not find config parameter'
    config = ConfigParser.RawConfigParser(dict_type=MultiOrderedDict)
    config.read([path])


class TestEnv:
    def test_config_set(self):
        checkConfigForDuplicates()

        checkConfig('ckanext.odsh.upload_formats', minLength=2)
        checkConfig('ckanext.dcat.rdf.profiles',
                    'odsheuro_dcat_ap odshdcatap_de')
        checkConfig('ckan.harvest.mq.type', 'redis')
        checkConfigDir('cache_dir')
        checkConfig('beaker.session.key', expected='ckan')
        checkConfig('beaker.session.secret')

        # who.config_file = %(here)s/who.ini
        # who.log_file = %(cache_dir)s/who_log.ini

        checkConfig('ckan.site_url')
        checkConfig('ckan.site_title', 'Open Data Portal Schleswig-Holstein')

        checkConfig('ckan.site_intro_text',
                    '#Willkommen auf Open Data Portal Schleswig-Holstein.')

        if isMaster():
            checkConfigDir('ckan.storage_path')

        if isSlave():
            checkConfig('ckanext.spatial.search_backend', 'solr-spatial-field')
            checkConfig('ckanext.spatial.common_map.type', 'wms')
            checkConfig('ckanext.spatial.common_map.wms.url',
                        'https://sg.geodatenzentrum.de/wms_webatlasde.light_grau')
            checkConfig('ckanext.spatial.common_map.wms.layers',
                        'webatlasde.light_grau')

        if isMaster():
            checkJsonFile(
                'qa.resource_format_openness_scores_json', expectedLength=60)

    def test_non_critical(self):
        checkConfig('who.timeout', '1800')

    def test_plugins(self):
        value = config.get('ckan.plugins', [])
        for p in ['odsh_dcat_harvest', 'odsh', 'odsh_harvest']:
            assert p in value, 'missing plugin:' + p

        if isMaster():
            for p in ['odsh_icap']:
                assert p in value, 'missing plugin:' + p

        # pdb.set_trace()

    def test_licenses(self):
        value = checkConfig('licenses_group_url')
        # assert 'ckanext-odsh' in value

        register = model.Package.get_license_register()
        licenses = register.values()

        assert len(licenses) > 15
        assert sum(['dcat' in l.id for l in licenses]) == 23

    def test_dcat_formats(self):
        checkConfigFile('ckan.odsh.resource_formats_fallback_filepath')
        profiles.resource_formats()
        assert len(profiles._RESOURCE_FORMATS_IMPORT) > 120

    def test_matomo(self):
        checkConfig('ckanext.odsh.matomo_id', expected='3')
        checkConfigUrl('ckanext.odsh.matomo_url',
                       responseContains='This resource is part of Matomo')
