import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckanext.dcat.interfaces import IDCATRDFHarvester
from ckanext.dcatde.extras import Extras

from ckanext.odsh.helper_pkg_dict import HelperPgkDict

from ckan import model

import ckan.plugins as p

_ = toolkit._

import logging
log = logging.getLogger(__name__)


class OdshDCATHarvestPlugin(plugins.SingletonPlugin):
    plugins.implements(IDCATRDFHarvester, inherit=True)
    
    def before_update(self, harvest_object, dataset_dict, temp_dict):
        existing_package_dict = self._get_existing_dataset(harvest_object.guid)
        new_dataset_extras = Extras(dataset_dict['extras'])
        if new_dataset_extras.key('modified') and \
                new_dataset_extras.value('modified') < existing_package_dict.get('metadata_modified'):
            log.info("Modified date of new dataset is not newer than "
                     + "the already exisiting dataset, ignoring new one.")
            dataset_dict.clear()

    def _get_existing_dataset(self, guid):
        '''
        Checks if a dataset with a certain guid extra already exists
        Returns a dict as the ones returned by package_show
        '''
        datasets = model.Session.query(model.Package.id) \
                                .join(model.PackageExtra) \
                                .filter(model.PackageExtra.key == 'guid') \
                                .filter(model.PackageExtra.value == guid) \
                                .filter(model.Package.state == 'active') \
                                .all()

        if not datasets:
            return None
        elif len(datasets) > 1:
            log.error('Found more than one dataset with the same guid: {0}'
                      .format(guid))
        return p.toolkit.get_action('package_show')({}, {'id': datasets[0][0]})


    def after_create(self, harvest_object, dataset_dict, temp_dict):
        '''
        Called just after a successful ``package_create`` action has been
        performed.

        This method sets relationships between packages and collections.
        '''
        dd = HelperPgkDict(dataset_dict)
        if dd.is_collection():
            dd.update_relations_to_collection_members()
            dd.add_uri_to_store()
        if dd.shall_be_part_of_collection():
            dd.update_relation_to_collection()
            dd.add_uri_to_store()
    
    
