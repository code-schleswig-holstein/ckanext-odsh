from ckan.common import config
import ckan.tests.helpers as helpers
import ckan.model as model
import pdb
import json
import ckanext.odsh.profiles as profiles

# run with nosetests --ckan --nologcapture --with-pylons=<config to test> ckanext/odsh/tests/test_env.py


class TestEnv:
    def test_config_set(self):
        value = config.get('ckanext.odsh.upload_formats', [])
        assert len(value) > 2

        value = config.get('ckanext.dcat.rdf.profiles')
        assert value.strip() == "odsheuro_dcat_ap odshdcatap_de"

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

    def test_qa_json(self):
        value = config.get('qa.resource_format_openness_scores_json', None)
        assert value
        with open(value) as json_file:  
            data = json.load(json_file)
            assert len(data)>60


    def test_dcat_formats(self):
        value = config.get('ckan.odsh.resource_formats_fallback_filepath', None)
        assert value

        with open(value.replace('file://','') +'.test', 'w') as fp:
            pass 

        profiles.resource_formats()

