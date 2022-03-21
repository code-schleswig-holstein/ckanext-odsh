import rdflib

from ckan.common import config
import ckan.lib.helpers as helpers
import ckan.model as model
from ckanext.dcat.profiles import DCT
from ckanext.dcat.utils import resource_uri
import ckanext.dcatde.dataset_utils as ds_utils
from ckanext.dcatde.profiles import DCATdeProfile, DCATDE, DCAT, DCATDE_1_0, DCATDE_1_0_1, DCATDE_1_0_2

import ckanext.odsh.helpers_tpsh as helpers_tpsh
import ckanext.odsh.collection.helpers as helpers_collection


DCT = rdflib.namespace.Namespace("http://purl.org/dc/terms/")
DCAT = rdflib.namespace.Namespace("http://www.w3.org/ns/dcat#")


class ODSHDCATdeProfile(DCATdeProfile):

    # from RDF

    def parse_dataset(self, dataset_dict, dataset_ref):
        dataset_dict = super(ODSHDCATdeProfile, self).parse_dataset(
            dataset_dict, dataset_ref
        )
        self._parse_distributions(dataset_dict, dataset_ref)
        self._parse_type(dataset_dict, dataset_ref)
        if self._belongs_to_collection(dataset_dict, dataset_ref):
            self._mark_for_adding_to_ckan_collection(dataset_dict, dataset_ref)
        return dataset_dict

    def _parse_distributions(self, dataset_dict, dataset_ref):
        for distribution in self.g.objects(dataset_ref, DCAT.distribution):
            for resource_dict in dataset_dict.get('resources', []):
                # Match distribution in graph and distribution in ckan-dict
                if unicode(distribution) == resource_uri(resource_dict):
                    for namespace in [DCATDE, DCATDE_1_0, DCATDE_1_0_1, DCATDE_1_0_2]:
                        value = self._object_value(
                            distribution, namespace.licenseAttributionByText)
                        if value:
                            ds_utils.insert_new_extras_field(
                                dataset_dict, 'licenseAttributionByText', value)
                            return

    def _parse_type(self, dataset_dict, dataset_ref):
        dct_type = self._object(dataset_ref, DCT.type)
        if dct_type:
            ckan_type = helpers_tpsh.map_dct_type_to_ckan_type(str(dct_type))
            dataset_dict.update({'type': ckan_type})

    def _belongs_to_collection(self, dataset_dict, dataset_ref):
        dct_is_version_of = self._object(dataset_ref, DCT.isVersionOf)
        belongs_to_collection = True if dct_is_version_of else False
        return belongs_to_collection

    def _mark_for_adding_to_ckan_collection(self, dataset_dict, dataset_ref):
        dataset_dict.update({'add_to_collection': True})

    # to RDF

    def graph_from_dataset(self, dataset_dict, dataset_ref):
        '''
        this class inherits from ODSHDCATdeProfile
        it has been extended to add information to
        the rdf export

        '''
        super(ODSHDCATdeProfile, self).graph_from_dataset(
            dataset_dict, dataset_ref)
        self._add_contributor_id(dataset_dict, dataset_ref)
        self._add_license_attribution_by_text(dataset_dict, dataset_ref)
        self._add_type(dataset_dict, dataset_ref)
        self._add_modified_and_issued(dataset_dict, dataset_ref)
        if self._is_dataset_collection(dataset_dict):
            self._remove_predefined_collection_members()
            self._add_collection_members(dataset_dict, dataset_ref)
        if self._dataset_belongs_to_collection(dataset_dict):
            self._add_collection(dataset_dict, dataset_ref)

    def _add_contributor_id(self, dataset_dict, dataset_ref):
        contributorID = 'http://dcat-ap.de/def/contributors/schleswigHolstein'
        self.g.add(
            (dataset_ref, DCATDE.contributorID,
                rdflib.URIRef(contributorID)
             )
        )

    def _add_license_attribution_by_text(self, dataset_dict, dataset_ref):
        licenseAttributionByText = self._get_dataset_value(
            dataset_dict, 'licenseAttributionByText')
        if licenseAttributionByText:
            self.g.set(
                (dataset_ref, DCATDE.licenseAttributionByText,
                 rdflib.Literal(licenseAttributionByText))
            )
            for distribution in self.g.objects(dataset_ref, DCAT.distribution):
                self.g.set(
                    (distribution, DCATDE.licenseAttributionByText,
                     rdflib.Literal(licenseAttributionByText))
                )

    def _add_modified_and_issued(self, dataset_dict, dataset_ref):
        '''
        Adds distributions last_modified and created values to
        dcat:modified and dcat:issued.
        '''
        for distribution in self.g.objects(dataset_ref, DCAT.distribution):
            for resource_dict in dataset_dict.get('resources', []):
                # Match distribution in graph and distribution in ckan-dict
                if unicode(distribution) == resource_uri(resource_dict):
                    last_modified = resource_dict.get('last_modified', None)
                    if last_modified:
                        self.g.set(
                            (distribution, DCT.modified, rdflib.Literal(
                                last_modified, datatype="http://www.w3.org/2001/XMLSchema#dateTime"))
                        )
                    created = resource_dict.get('created', None)
                    if created:
                        self.g.set(
                            (distribution, DCT.issued, rdflib.Literal(
                                created, datatype="http://www.w3.org/2001/XMLSchema#dateTime"))
                        )

    def _add_type(self, dataset_dict, dataset_ref):
        '''
        adds the type if there is a known mapping from ckan type to
        dct:type
        '''
        ckan_type = self._get_ckan_type(dataset_dict)
        dct_type = helpers_tpsh.map_ckan_type_to_dct_type(ckan_type)
        if dct_type:
            self.g.set(
                (dataset_ref, DCT.type,
                    rdflib.URIRef(dct_type)
                 )
            )

    def _get_ckan_type(self, dataset_dict):
        ckan_type = self._get_dataset_value(dataset_dict, 'type')
        return ckan_type

    def _remove_predefined_collection_members(self):
        for s, p, o in self.g:
            if p == DCT.hasVersion:
                self.g.remove((s, p, o))

    def _add_collection_members(self, dataset_dict, dataset_ref):
        dataset_refs_belonging_to_collection = self._get_dataset_refs_belonging_to_collection(
            dataset_dict)
        for ref in dataset_refs_belonging_to_collection:
            self.g.add(
                (dataset_ref, DCT.hasVersion, rdflib.URIRef(ref))
            )

    def _is_dataset_collection(self, dataset_dict):
        ckan_type = self._get_ckan_type(dataset_dict)
        is_collection = ckan_type == 'collection'
        return is_collection

    def _get_dataset_refs_belonging_to_collection(self, dataset_dict):
        dataset_names = helpers_collection.get_dataset_names(dataset_dict)
        dataset_dicts = [model.Package.get(
            name).as_dict() for name in dataset_names]
        dataset_ids = [dataset_dict.get('id')
                       for dataset_dict in dataset_dicts]
        dataset_refs = [self._construct_refs(id) for id in dataset_ids]
        return dataset_refs

    @staticmethod
    def _construct_refs(id):
        public_url = config.get('ckan.site_url')
        url_to_id = helpers.url_for(controller='package', action='read', id=id)
        ref = public_url + url_to_id
        return ref

    def _dataset_belongs_to_collection(self, dataset_dict):
        '''
        returns True if a containing collection is found
        '''
        if dataset_dict.get('type') == 'collection':
            return False
        collection_name = helpers_collection.get_collection_id(dataset_dict)
        return collection_name is not None

    def _add_collection(self, dataset_dict, dataset_ref):
        collection_id = helpers_collection.get_collection_id(dataset_dict)
        collection_uri = self._construct_refs(collection_id)
        self.g.set(
            (dataset_ref, DCT.isVersionOf,
                rdflib.URIRef(collection_uri)
             )
        )