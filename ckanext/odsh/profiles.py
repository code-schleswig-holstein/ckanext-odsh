from ckanext.dcatde.profiles import DCATdeProfile, DCATDE, DCAT, VCARD, dcat_theme_prefix 
from ckanext.dcat.utils import resource_uri
from ckanext.dcat.profiles import EuropeanDCATAPProfile, DCT
from ckan.model.license import LicenseRegister
import ckanext.dcatde.dataset_utils as ds_utils

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
        """ Transforms DCAT-AP.de-Data to CKAN-Dictionary """

        # Simple additional fields
        for key, predicate in (
               ('qualityProcessURI', DCATDE.qualityProcessURI),
               ('metadata_original_html', DCAT.landingPage),
               ('politicalGeocodingLevelURI', DCATDE.politicalGeocodingLevelURI),
               ):
            value = self._object_value(dataset_ref, predicate)
            if value:
                ds_utils.insert_new_extras_field(dataset_dict, key, value)

        # List fields
        for key, predicate, in (
               ('contributorID', DCATDE.contributorID),
               ('politicalGeocodingURI', DCATDE.politicalGeocodingURI),
               ('legalbasisText', DCATDE.legalbasisText),
               ('geocodingText', DCATDE.geocodingText),
               ):
            values = self._object_value_list(dataset_ref, predicate)
            if values:
                ds_utils.insert_new_extras_field(dataset_dict, key, json.dumps(values))

        self._parse_contact(dataset_dict, dataset_ref, DCATDE.originator, 'originator', True)
        self._parse_contact(dataset_dict, dataset_ref, DCATDE.maintainer, 'maintainer', False)
        self._parse_contact(dataset_dict, dataset_ref, DCT.contributor, 'contributor', True)
        self._parse_contact(dataset_dict, dataset_ref, DCT.creator, 'author', False)

        # dcat:contactPoint
        # TODO: dcat-ap adds the values to extras.contact_... . Maybe better than maintainer?
        contact = self._object(dataset_ref, DCAT.contactPoint)
        self._add_maintainer_field(dataset_dict, contact, 'url', VCARD.hasURL)

        contact_tel = self._object_value(contact, VCARD.hasTelephone)
        if contact_tel:
            ds_utils.insert(dataset_dict, 'maintainer_tel', self._without_tel(contact_tel), True)

        self._add_maintainer_field(dataset_dict, contact, 'street', VCARD.hasStreetAddress)
        self._add_maintainer_field(dataset_dict, contact, 'city', VCARD.hasLocality)
        self._add_maintainer_field(dataset_dict, contact, 'zip', VCARD.hasPostalCode)
        self._add_maintainer_field(dataset_dict, contact, 'country', VCARD.hasCountryName)

        # Groups
        groups = self._get_dataset_value(dataset_dict, 'groups')

        if not groups:
            groups = []

        for obj in self.g.objects(dataset_ref, DCAT.theme):
            current_theme = unicode(obj)

            if current_theme.startswith(dcat_theme_prefix):
                group = current_theme.replace(dcat_theme_prefix, '').lower()
                groups.append({'id': group, 'name': group})

        dataset_dict['groups'] = groups

        # Add additional distribution fields
        hasAttr = False
        for distribution in self.g.objects(dataset_ref, DCAT.distribution):
            for resource_dict in dataset_dict.get('resources', []):
                # Match distribution in graph and distribution in ckan-dict
                if unicode(distribution) == resource_uri(resource_dict):
                    for key, predicate in (
                            ('licenseAttributionByText', DCATDE.licenseAttributionByText),
                            ('plannedAvailability', DCATDE.plannedAvailability)
                    ):
                        value = self._object_value(distribution, predicate)
                        if value:
                            ds_utils.insert_resource_extra(resource_dict, key, value)
                            if not hasAttr and key == 'licenseAttributionByText':
                                ds_utils.insert_new_extras_field(dataset_dict, key, value)
                                hasAttr = True

        return dataset_dict