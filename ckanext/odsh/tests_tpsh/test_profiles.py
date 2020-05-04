import nose.tools as nt
import rdflib
from rdflib import Graph
from mock import patch

from ckanext.dcat.profiles import URIRefOrLiteral

import ckanext.odsh.profiles as profiles
import ckanext.odsh.helper_pkg_dict as helper_pkg_dict

DCT = rdflib.namespace.Namespace("http://purl.org/dc/terms/")


class TestODSHDCATdeProfileParseDatasetWithCollection(object):
    '''
    Tests for ODSHDCATdeProfile.parse_dataset with an rdf file 
    containing a collection
    '''
    def setUp(self):
        rdf_graph = Graph()
        rdf_graph.parse('ckanext/odsh/tests_tpsh/resources/collection1.rdf')
        self.profile = profiles.ODSHDCATdeProfile(rdf_graph)
        self.dataset_ref_with_collection = URIRefOrLiteral(
            'http://opendata.schleswig-holstein.de/dataset/LAsDSH_SER_Statistik_anerkannte_Versorgungsberechtigte'
        )
        self.dataset_ref_with_collection_member = URIRefOrLiteral(
            'http://opendata.schleswig-holstein.de/dataset/LAsDSH_SER_Statistik_anerkannte_Versorgungsberechtigte_Monat_201704'
        )
        self.dataset_ref_with_member_not_in_collection = URIRefOrLiteral(
            'http://opendata.schleswig-holstein.de/dataset/Test_nicht_in_Collection'
        )
    
    def test_parse_dataset_adds_type_collection_to_dataset_dict(self):
        dataset_dict = {}
        self.profile.parse_dataset(dataset_dict, self.dataset_ref_with_collection)
        nt.assert_equal('collection', dataset_dict['type'])
    
    def test_parse_dataset_adds_flag_for_collection_member(self):
        dataset_dict = {}
        self.profile.parse_dataset(dataset_dict, self.dataset_ref_with_collection_member)
        nt.assert_equal(True, dataset_dict.get('add_to_collection'))
    
    def test_parse_type_adds_type_collection_to_dataset_dict(self):
        dataset_dict = {}
        self.profile._parse_type(dataset_dict, self.dataset_ref_with_collection)
        nt.assert_equal('collection', dataset_dict['type'])

    def test_parse_type_does_not_add_collection_to_dataset_dict(self):
        dataset_dict = {}
        self.profile._parse_type(dataset_dict, self.dataset_ref_with_collection_member)
        nt.assert_not_in('type', dataset_dict)

    def test_belongs_to_collection_returns_true(self):
        dataset_dict = {}
        assert self.profile._belongs_to_collection(dataset_dict, self.dataset_ref_with_collection_member)

    def test_belongs_to_collection_returns_false(self):
        dataset_dict = {}
        belongs_to_collection = self.profile._belongs_to_collection(
            dataset_dict, self.dataset_ref_with_member_not_in_collection)
        nt.assert_false(belongs_to_collection)
    

class TestODSHDCATdeProfileParseDatasetWithSubject(object):
    '''
    Tests for ODSHDCATdeProfile.parse_dataset with an rdf file 
    containing datasets with subjects
    '''
    def setUp(self):
        rdf_graph = Graph()
        rdf_graph.parse('ckanext/odsh/tests_tpsh/resources/transparenz.rdf')
        self.profile = profiles.ODSHDCATdeProfile(rdf_graph)
        self.dataset_ref_with_subject = URIRefOrLiteral(
            'http://transparenz.schleswig-holstein.de/ae2a3cffda84388365bc87711ed4af47'
        )

    def test_parse_subject_returns_subject(self):
        dataset_dict = {}
        self.profile._parse_subject(dataset_dict, self.dataset_ref_with_subject)
        nt.assert_equal('http://d-nb.info/gnd/4128022-2', dataset_dict['subject'])
    
    def test_parse_dataset_returns_subject(self):
        dataset_dict = {}
        self.profile.parse_dataset(dataset_dict, self.dataset_ref_with_subject)
        nt.assert_equal('http://d-nb.info/gnd/4128022-2', dataset_dict['subject'])


class TestODSHDCATdeProfileGraphFromDataset(object):
    '''
    Tests for ODSHDCATdeProfile.graph_from_dataset
    '''
    def setUp(self):
        rdf_graph = Graph()
        self.profile = profiles.ODSHDCATdeProfile(rdf_graph)
        self.dummy_dataset_ref = URIRefOrLiteral('http://some_ref')
    
    def get_graph_and_assert_in(self, dataset_dict, dataset_ref, expected_node):
        self.profile.graph_from_dataset(dataset_dict, dataset_ref)
        graph_serialized = self.profile.g.serialize()
        print(self.profile.g.serialize(format='pretty-xml'))
        nt.assert_in(expected_node, graph_serialized)
    
    
    patch_collection_member = patch.object(
        profiles.ODSHDCATdeProfile, 
        '_dataset_belongs_to_collection', 
        return_value=True
    )
    
    patch_no_collection_member = patch.object(
        profiles.ODSHDCATdeProfile, 
        '_dataset_belongs_to_collection', 
        return_value=False
    )

    
    @patch_no_collection_member
    def test_it_adds_dct_subject(self, __):
        dataset_dict = {
            'subject': 'http://some_subject',
            'type': 'dataset',
            'groups': [],
        }        
        expected_node = '<dct:subject rdf:resource="http://some_subject"/>'
        self.get_graph_and_assert_in(dataset_dict, self.dummy_dataset_ref, expected_node)
    
    
    @patch_no_collection_member
    def test_it_adds_dct_type_collection(self, __):
        dataset_dict = {
            'groups': [],
            'type': 'collection',
        }
        expected_node = (
            '<dct:type rdf:resource="http://dcat-ap.de/def/datasetTypes/collection"/>'
        )
        with patch.object(
            profiles.ODSHDCATdeProfile, 
            '_get_dataset_refs_belonging_to_collection', 
            return_value=[]
        ):
            self.get_graph_and_assert_in(dataset_dict, self.dummy_dataset_ref, expected_node)
    
    
    @patch_no_collection_member
    def test_it_adds_members_of_collection(self, __):
        '''
        tests if rdf export of a collection  contains the members of that collection.
        The members are read from the package relationships.
        '''
        dataset_dict = {
            'groups': [],
            'type': 'collection',
        }
        expected_nodes = (
            '<dct:hasVersion rdf:resource="http://id_1"/>',
            '<dct:hasVersion rdf:resource="http://id_2"/>',
        )
        # mock get_dataset_refs_belonging_to_collection(context, collection_name)
        dataset_refs_belonging_to_collection = ['http://id_1', 'http://id_2']
        with patch.object(
            profiles.ODSHDCATdeProfile, 
            '_get_dataset_refs_belonging_to_collection', 
            return_value=dataset_refs_belonging_to_collection
        ):
            for expected_node in expected_nodes:
                self.get_graph_and_assert_in(dataset_dict, self.dummy_dataset_ref, expected_node)
    
    def test_remove_predefined_collection_members(self):
        rdf_graph = Graph()
        self.profile = profiles.ODSHDCATdeProfile(rdf_graph)
        dummy_ref = rdflib.URIRef('http://transparenz.schleswig-holstein.de/5ffd27c528f7ab6936318da90d5cdd63')
        refs = (
            'http://transparenz.schleswig-holstein.de/9bbeaf7b503dbd2c667786db08c4512d',
            'http://transparenz.schleswig-holstein.de/f6de9c145fe28effe99fc163b92d657e'
        )
        for ref in refs:
            self.profile.g.add(
                (dummy_ref, DCT.hasVersion, rdflib.URIRef(ref))
            )
        self.profile._remove_predefined_collection_members()
        graph_serialized = self.profile.g.serialize()
        for ref in refs:
            nt.assert_not_in(ref, graph_serialized)