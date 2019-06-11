from rdflib.namespace import Namespace, RDF, XSD, SKOS, RDFS
import rdflib
import ckan.tests.factories as factories
from ckan.common import config
import ckan.model as model
import json
import ckanext.odsh.profiles as profiles
import urllib2
import ckan.tests.helpers as helpers
from ckan.common import config
import ckan.config.middleware
from ckanext.dcatde.profiles import DCATDE, DCAT, DCATDE_1_0
import pdb


# run with nosetests --ckan --nologcapture --with-pylons=<config to test> ckanext/odsh/tests/test_routes.py

DCAT = Namespace("http://www.w3.org/ns/dcat#")
DCT = Namespace("http://purl.org/dc/terms/")


def _get_test_app():
    app = ckan.config.middleware.make_app(config['global_conf'], **config)
    app = helpers.CKANTestApp(app)
    return app


class TestRDFExport:

    def test_upload_empty_form_fails(self):
        # arrange
        extras = [
            {'key': 'temporal_start', 'value': '2000-01-27'},
            {'key': 'temporal_end', 'value': '2000-01-27'},
            {'key': 'issued', 'value': '2000-01-27'},
            {'key': 'spatial_uri',
                'value': 'http://dcat-ap.de/def/politicalGeocoding/districtKey/01001'},
            {'key': 'licenseAttributionByText', 'value': 'text'},
            {'key': 'groups', 'value': 'soci'},
        ]
        user = {'name': 'ckanuser'}
        dataset = factories.Dataset(user=user,
                                    name='testname',
                                    title='Test Title',
                                    issued='27-01-2000',
                                    extras=extras,
                                    owner_org='test',
                                    license_id="http://dcat-ap.de/def/licenses/dl-by-de/2.0",
                                    licenseAttributionByText='foo')
        factories.Resource(
            package_id=dataset['id'], license=dataset['license_id'], licenseAttributionByText='foo')
        factories.Resource(
            package_id=dataset['id'])

        g = rdflib.Graph()
        response = self._get_app().get('/dataset/'+dataset['name']+'.rdf')
        g.parse(data=response.body)
        lic = self._extract_licenses(g)
        att = self._extract_licenseAttributions(g)

        assert len(lic) == 3
        assert len(att) == 3
        assert len(set([str(l) for l in lic])) == 1
        assert len(set([str(a) for a in att])) == 1
        assert str(att[0]) == 'text'

    def test_catalog(self):
        g = rdflib.Graph()
        response = self._get_app().get('/catalog.xml')
        g.parse(data=response.body)
        datasets = list(g.subjects(RDF.type, DCAT.Dataset))

        response = self._get_app().get('/api/3/action/package_search')
        plist = json.loads(response.body)

        assert len(datasets) == plist['result']['count'], "{rdf} != {cat}".format(
            rdf=len(datasets), cat=plist['result']['count'])

    def _get_app(self):
        if not hasattr(self, 'app'):
            app = _get_test_app()
            self.app = app
        return self.app

    def _extract_licenses(self, g):

        datasets = list(g.subjects(RDF.type, DCAT.Dataset))
        assert len(datasets) == 1
        dataset = datasets[0]

        ret = list(g.objects(dataset, DCT.license))

        distributions = list(g.objects(dataset, DCAT.distribution))
        for d in distributions:
            for l in g.objects(d, DCT.license):
                ret.append(l)

        return ret

    def _extract_licenseAttributions(self, g):

        datasets = list(g.subjects(RDF.type, DCAT.Dataset))
        assert len(datasets) == 1
        dataset = datasets[0]

        ret = []
        for namespace in [DCATDE, DCATDE_1_0]:
            ret += list(g.objects(dataset, namespace.licenseAttributionByText))

        distributions = list(g.objects(dataset, DCAT.distribution))
        for d in distributions:
            for namespace in [DCATDE, DCATDE_1_0]:
                ret += list(g.objects(d, namespace.licenseAttributionByText))

        return ret
