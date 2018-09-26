from ckan import model
from ckan.logic import get_action
from ckan.plugins import toolkit
from ckanext.harvest.harvesters.base import HarvesterBase
from ckanext.harvest.model import HarvestObject

import requests
import uuid
import traceback
import json
import logging
import datetime

log = logging.getLogger(__name__)


class KielHarvester(HarvesterBase):
    '''
    A Harvester for Kiel Open Data
    '''

    @staticmethod
    def info():
        return {
            'name': 'kiel',
            'title': 'Kiel Open Data',
            'description': 'Harvests Kiel Open Data',
            'form_config_interface': 'Text'
        }

    def gather_stage(self, harvest_job):
        url = harvest_job.source.url
        datasets = requests.get(url=url).json()

        try:
            used_identifiers = []
            ids = []
            for dataset in datasets:
                guid = str(uuid.uuid3(uuid.NAMESPACE_URL, dataset.get("url").encode('ascii', 'ignore')))
                obj = HarvestObject(job=harvest_job, guid=guid)
                obj.content = json.dumps(dataset)
                obj.save()
                log.info("harvest_object_id: %s, GUID: %s successfully gathered " % (str(obj.id), str(obj.guid)))
                used_identifiers.append(guid)
                ids.append(obj.id)

        except Exception as e:
            self._save_gather_error(
                'Statistik-Nord-Harvester: Error gathering the identifiers from the source server [%s]' % str(e),
                harvest_job)
            log.error(e)
            return None

        if len(ids) > 0:
            log.info(
                "finished %s IDs of %s IDs successfully gathered" % (len(used_identifiers), len(datasets)))
            log.debug("List of gathered IDs: %s" % ids)
            log.debug("gather_stage() finished: %s IDs gathered" % len(ids))
            return ids
        else:
            log.error("No records received")
            self._save_gather_error("Couldn't find any metadata files", harvest_job)
            return None

    @staticmethod
    def fetch_stage(harvest_object):
        if harvest_object:
            return True
        else:
            return False

    def import_stage(self, harvest_object):
        context = {
            'model': model,
            'session': model.Session,
            'user': self._get_user_name(),
        }
        if not harvest_object:
            log.error('Kiel-Harvester: No harvest object received')
            return False

        if harvest_object.content is None:
            self._save_object_error('Empty content for object %s' % harvest_object.id, harvest_object, u'Import')
            return False
        else:
            package_dict = json.loads(harvest_object.content)
            published = str()
            for date in package_dict['extras']['dates']:
                if date['role'] == 'veroeffentlicht':
                    published = date['date']
            package_dict['metadata_modified'] = datetime.datetime.strptime(published, "%d.%m.%Y").isoformat()
            source_dataset = get_action('package_show')(context.copy(), {'id': harvest_object.source.id})
            package_dict['owner_org'] = source_dataset.get('owner_org')

            if package_dict['type'] == 'datensatz':
                package_dict['type'] = 'dataset'
            package_dict['id'] = harvest_object.guid
            package_dict['groups'] = list()
            package_dict['extras'] = list()

            tags = package_dict['tags']
            package_dict['tags'] = list()
            for tag in tags:
                seperated_tags = tag.split(',')
                for seperated_tag in seperated_tags:
                    if seperated_tag != '' and len(seperated_tag) < 100:
                        package_dict['tags'].append({'name': seperated_tag.strip()})

#            log.debug(json.dumps(package_dict))
            try:
                result = self._create_or_update_package(package_dict, harvest_object, package_dict_form='package_show')
                return result
            except toolkit.ValidationError as e:
                self._save_object_error('Validation Error: %s' % str(e.error_summary), harvest_object, 'Import')
                return False