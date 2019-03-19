from ckanext.dcatde.profiles import DCATdeProfile
from ckanext.dcat.profiles import EuropeanDCATAPProfile, DCT
from ckan.model.license import LicenseRegister

class ODSHDCATdeProfile(EuropeanDCATAPProfile):

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
