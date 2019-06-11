from ckanext.odsh.tests.test_helpers import AppProxy
import ckanext.odsh.tests.test_helpers as testhelpers
import ckan.tests.factories as factories
import uuid
import pdb
from ckanext.odsh.tests.harvest_sever_mock import HarvestServerMock
import ckanext.odsh.tests.harvest_sever_mock as harvest_sever_mock
import subprocess


class TestHarvest:

    def _create_harvester(self, source_type):
        guid = str(uuid.uuid4())
        # self.org = factories.Organization(
        #     name="test_harvest_org_" + guid,
        #     users=[{'name': 'ckanuser', 'capacity': 'admin'}]
        # )
        self._get_app().login()
        response = self.app.get('/harvest/new')
        form = response.forms[0]
        title = 'harvest_test_source_' + guid
        form['title'] = title
        form['url'] = "http://localhost:5002/" + guid 
        form['source_type'] = source_type 
        final_response = self.app.submit_form(form)
        # submit_response = self.app.submit_form(form)
        # assert 'missing value' in submit_response
        assert 'There are no datasets associated to this harvest source.' in final_response
        return title

    def notest_create_harvester(self):
        self._create_harvester()

    def test_harvest_dcat(self):
        # Arrange
        harvester = self._create_harvester('dcat_rdf')
        harvest_sever_mock.data = self._load_rdf_catalog()
        server = HarvestServerMock()
        server.start()
        self.run_harvest(harvester)
        # server.stop()

    def run_harvest(self, harvester):
        out = subprocess.check_output([
            "paster", "--plugin=ckanext-harvest", "harvester", "run_test", harvester,   '--config='+testhelpers.getConfigPath()])

    def _get_app(self):
        if not hasattr(self, 'app'):
            app = AppProxy()
            self.app = app
        return self.app

    def _load_rdf_catalog(self):
        with open('ckanext/odsh/tests/rdf_catalog.xml', 'r') as rdffile:
            data = rdffile.read()
            return data
