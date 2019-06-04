from ckan.common import config
import ckan.tests.helpers as helpers
import ckan.model as model
import pdb

# run with nosetests --ckan --nologcapture --with-pylons=<config to test> ckanext/odsh/tests/test_env.py


class TestEnv(helpers.FunctionalTestBase):
    def test_config_set(self):
        value = config.get('ckanext.odsh.upload_formats', [])
        assert len(value) > 2

        value = config.get('ckan.plugins', [])
        for p in ['odsh_dcat_harvest', 'odsh', 'odsh_icap', 'odsh_harvest']:
            assert p in value
        # pdb.set_trace()

    def test_licenses(self):
        value = config.get('licenses_group_url')
        assert 'ckanext-odsh' in value

        register = model.Package.get_license_register()
        licenses = register.values()

        assert len(licenses) > 15
        assert sum(['dcat' in l.id for l in licenses]) == 23
