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
from urlparse import urlsplit

expected_commit = '8cd9576884cae6abe50a27c891434cb9fe87ced2'

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


def readUrl(value):
    req = urllib2.Request(value)
    response = urllib2.urlopen(req)
    data = response.read()
    return data


def checkConfigUrl(key, expectedKey=None, responseContains=None):
    value = checkConfig(key, expected=expectedKey)
    data = readUrl(value)
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
                     os.W_OK), "expected '{key}={val}' to be writeable (user was '{user}')".format(key=key, val=value, user=os.getlogin())


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

        checkConfig('ckanext.dcat.rdf.profiles',
                    'odsheuro_dcat_ap odshdcatap_de')
        # checkConfigDir('cache_dir')
        checkConfig('beaker.session.key', expected='ckan')
        checkConfig('beaker.session.secret')

        # who.config_file = %(here)s/who.ini
        # who.log_file = %(cache_dir)s/who_log.ini

        checkConfig('ckan.site_url')
        checkConfig('ckan.site_title', 'Open Data Schleswig-Holstein')

        checkConfig('ckan.site_intro_text',
                    '#Willkommen auf Open Data Portal Schleswig-Holstein.')

        if isMaster():
            checkConfigDir('ckan.storage_path')
            checkConfig('ckanext-archiver.user_agent_string',
                        'Open Data Schleswig-Holstein')
            checkConfig('ckan.harvest.mq.type', 'redis')

        if isSlave():
            checkConfig('ckanext.odsh.upload_formats', minLength=2)
            checkConfig('ckanext.spatial.search_backend', 'solr-spatial-field')
            checkConfig('ckanext.spatial.common_map.type', 'wms')
            checkConfig('ckanext.spatial.common_map.wms.url',
                        'https://sg.geodatenzentrum.de/wms_webatlasde.light_grau')
            checkConfig('ckanext.spatial.common_map.wms.layers',
                        'webatlasde.light_grau')

        if isMaster():
            checkJsonFile(
                'qa.resource_format_openness_scores_json', expectedLength=60)

        checkConfig('ckanext.odsh.language.mapping',
                    '/usr/lib/ckan/default/src/ckanext-odsh/languages.json')

    def test_non_critical(self):
        checkConfig('who.timeout', '1800')

    def test_plugins(self):
        value = config.get('ckan.plugins', [])
        for p in ['odsh']:
            assert p in value, 'missing plugin:' + p

        if isMaster():
            for p in ['odsh_icap', 'odsh_dcat_harvest', 'odsh_harvest']:
                assert p in value, 'missing plugin:' + p
        if isSlave():
            for p in ['odsh_autocomplete']:
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

    # def test_version(self):
    #     url = checkConfig('ckan.site_url')
    #     if url[-1] == '/':
    #         url = url[:-1]
    #     version = readUrl(url+'/api/3/action/resource_qv4yAI2rgotamXGk98gJ').strip()
    #     # version = checkConfig('ckanext.odsh.version')
    #     assert version == expected_commit, "wrong version: {was}!={exp}".format(was=version, exp=expected_commit)

    def test_routes(self):
        if isMaster():
            return

        expexted_rules = \
            """ ProxyPass /dataset/new http://10.61.47.219/dataset/new
    ProxyPassReverse /dataset/new http://10.61.47.219/dataset/new
    ProxyPassMatch ^/(dataset/delete/[^/]+)$ http://10.61.47.219/$1
    ProxyPassReverse ^/(dataset/delete/[^/]+)$ http://10.61.47.219/$1
    ProxyPassMatch ^/(dataset/edit/[^/]+)$ http://10.61.47.219/$1
    ProxyPassReverse ^/(dataset/edit/[^/]+)$ http://10.61.47.219/$1
    ProxyPassReverse /dataset http://141.91.184.90/dataset
    ProxyPassReverse /dataset http://141.91.184.90/dataset
    ProxyPass /dataset/new_resource http://10.61.47.219/dataset/new_resource
    ProxyPassReverse /dataset/new_resource http://141.91.184.90/dataset/new_resource
    ProxyPassReverse /dataset/new_resource http://141.91.184.90/dataset/new_resource
    #ProxyPass /api/i18n/de http://141.91.184.90/api/i18n/de
    ProxyPassReverse ^/uploads/group/(.*)$ http://10.61.47.219/uploads/group/$1
    ProxyPassMatch ^/uploads/group/(.*)$ http://10.61.47.219/uploads/group/$1
    ProxyPassReverse ^/(dataset/[^/]+/resource/[^/]+/download/[^/]+)$ http://141.91.184.90/$1
    ProxyPassMatch ^/(dataset/[^/]+/resource/[^/]+/download/[^/]+)$ http://141.91.184.90/$1
    ProxyPassReverse ^/(dataset/[^/]+/resource/[^/]+)$ http://10.61.47.219/$1
    ProxyPassMatch ^/(dataset/[^/]+/resource/[^/]+/)$ http://10.61.47.219/$1
    ProxyPassMatch ^/(dataset/[^/]+/resource_data/[^/]+)$ http://10.61.47.219/$1
    ProxyPassReverse ^/(dataset/[^/]+/resource_data/[^/]+)$ http://10.61.47.219/$1
    ProxyPassMatch ^/(dataset/[^/]+/resource/[^/]+/new_view[^/]*)$ http://10.61.47.219/$1
    ProxyPassReverse ^/(dataset/[^/]+/resource/[^/]+/new_view[^/]*)$ http://10.61.47.219/$1
    ProxyPassMatch ^/(harvest.*)$ http://141.91.184.90/$1
    ProxyPassReverse /harvest http://141.91.184.90/harvest
    ProxyPass /harvest http://141.91.184.90/harvest
    ProxyPassReverse ^/(harvest.*)$ http://141.91.184.90/$1
    ProxyPassReverse ^/(api/3/action/package.*)$ http://10.61.47.219/$1
    ProxyPassMatch ^/(api/3/action/package.*)$ http://10.61.47.219/$1
    ProxyPass /api/action/package_create http://10.61.47.219/api/action/package_create
    ProxyPassReverse /api/action/package_create http://10.61.47.219/api/action/package_create
    ProxyPass /api/action/resource_create http://10.61.47.219/api/action/resource_create
    ProxyPassReverse /api/action/resource_create http://10.61.47.219/api/action/resource_create
    ProxyPassMatch ^/(organization/edit/[^/]+)$ http://10.61.47.219/$1
    ProxyPassReverse ^/(organization/edit/[^/]+)$ http://10.61.47.219/$1 
    ProxyPass /organization/new http://<interne-IP-Master>/organization/new
    ProxyPassReverse /organization/new http://<interne-IP-Master>/organization/new
    ProxyPassReverse /organization http://<interne-IP-Master>/organization
    ProxyPassReverse ^/(organization/edit/[^/]+)$ http://<interne-IP-Master>/$1

    # ProxyPass /datarequest http://10.61.47.219/datarequest
    # ProxyPassReverse /datarequest http://10.61.47.219/datarequest
    """

        expected = self._parse_rules(expexted_rules.splitlines())

        # with open('ckan_default.conf', 'r') as aconfig:
        with open('/etc/apache2/sites-enabled/ckan_default.conf', 'r') as aconfig:
            lines = aconfig.readlines()
            # pdb.set_trace()
            current = self._parse_rules(lines, check_host=True)
            if len(expected.symmetric_difference(current)) > 0:
                diff = expected.difference(current)
                if len(diff) > 0:
                    print('WARNING: missing routes:')
                    for r in sorted(diff, key=lambda tup: tup[1]):
                        print('{cmd} {source} {target}'.format(
                            cmd=r[0], source=r[1], target='http://<interne-IP-Master>'+r[2]))
                diff = current.difference(expected)
                if len(diff) > 0:
                    print('WARNING: found unexpected routes:')
                    for r in sorted(diff, key=lambda tup: tup[1]):
                        print('{cmd} {source} {target}'.format(
                            cmd=r[0], source=r[1], target='<target>'+r[2]))

    def _parse_rules(self, lines, check_host=False):
        rules = set(['ProxyPassMatch', 'ProxyPassReverse', 'ProxyPass'])
        ret = []
        hosts = set()
        for line in lines:
            tokens = filter(lambda t: t.strip(), line.strip().split(' '))
            if not tokens or tokens[0] not in rules:
                continue
            assert len(tokens) == 3
            # for token in tokens:
            # print(token)
            f = urlsplit(tokens[2])
            ret.append((tokens[0], tokens[1], f.path))
            hosts.add(f.netloc)
        if check_host and len(hosts) > 1:
            print('WARNING: found multiple target hosts: {hosts}'.format(
                hosts=', '.join(hosts)))
        return set(ret)
