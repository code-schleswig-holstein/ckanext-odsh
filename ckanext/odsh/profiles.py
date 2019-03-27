from ckanext.dcatde.profiles import DCATdeProfile, DCATDE, DCAT, VCARD, dcat_theme_prefix , DCATDE_1_0
from ckanext.dcat.utils import resource_uri
from ckanext.dcat.profiles import EuropeanDCATAPProfile, DCT
from ckan.model.license import LicenseRegister
import ckanext.dcatde.dataset_utils as ds_utils
import logging

log = logging.getLogger(__name__)

class ODSHEuropeanDCATAPProfile(EuropeanDCATAPProfile):

    def _license(self, dataset_ref):
        if self._licenceregister_cache is not None:
            license_uri2id, license_title2id = self._licenceregister_cache
        else:
            license_uri2id = {}
            license_title2id = {}
            for license_id, license in LicenseRegister().items():
                license_uri2id[license_id] = license_id 
                license_uri2id[license.url] = license_id
                license_title2id[license.title] = license_id
            self._licenceregister_cache = license_uri2id, license_title2id

        for distribution in self._distributions(dataset_ref):
            # If distribution has a license, attach it to the dataset
            license = self._object(distribution, DCT.license)
            if license:
                # Try to find a matching license comparing URIs, then titles
                license_id = license_uri2id.get(license.toPython())
                if not license_id:
                    license_id = license_title2id.get(
                        self._object_value(license, DCT.title))
                if license_id:
                    return license_id
        return ''

class ODSHDCATdeProfile(DCATdeProfile):
    def parse_dataset(self, dataset_dict, dataset_ref):
        dataset_dict = super(ODSHDCATdeProfile,self).parse_dataset(dataset_dict, dataset_ref)
        # Enhance Distributions
        for distribution in self.g.objects(dataset_ref, DCAT.distribution):
            for resource_dict in dataset_dict.get('resources', []):
                # Match distribution in graph and distribution in ckan-dict
                if unicode(distribution) == resource_uri(resource_dict):
                    for namespace in [DCATDE, DCATDE_1_0]:
                        value = self._object_value(distribution, namespace.licenseAttributionByText)
                        if value:
                            ds_utils.insert_new_extras_field(dataset_dict, 'licenseAttributionByText', value)
                            return dataset_dict
        return dataset_dict
