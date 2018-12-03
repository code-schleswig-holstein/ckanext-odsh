import ckan.model as model
from ckanext.harvest.model import HarvestObject
from ckanext.harvest.harvesters.base import HarvesterBase


class ODSHBaseHarvester(HarvesterBase):
    def _get_license_id(self, license_id):
        license_mapping = {'dl-de-zero-2.0': 'http://dcat-ap.de/def/licenses/dl-zero-de/2.0',
                           'dl-de-by-2.0': "http://dcat-ap.de/def/licenses/dl-by-de/2.0"}
        return license_mapping.get(license_id, None)

    def _handle_current_harvest_object(self, harvest_object, package_id):
        # Get the last harvested object (if any)
        previous_object = model.Session.query(HarvestObject) \
                                       .filter(HarvestObject.guid==harvest_object.guid) \
                                       .filter(HarvestObject.current==True) \
                                       .first()

        # Flag previous object as not current anymore
        if previous_object:
            previous_object.current = False
            previous_object.add()

        # Flag this object as the current one
        harvest_object.current = True
        harvest_object.package_id = package_id
        harvest_object.add()

        model.Session.execute('SET CONSTRAINTS harvest_object_package_id_fkey DEFERRED')
        model.Session.flush()
