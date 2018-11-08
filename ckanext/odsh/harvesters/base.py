from ckanext.harvest.harvesters.base import HarvesterBase


class ODSHBaseHarvester(HarvesterBase):
    def _get_license_id(self, license_id):
        license_mapping = {'dl-de-zero-2.0': 'http://dcat-ap.de/def/licenses/dl-zero-de/2.0',
                           'dl-de-by-2.0': "http://dcat-ap.de/def/licenses/dl-by-de/2.0"}
        return license_mapping.get(license_id, None)
