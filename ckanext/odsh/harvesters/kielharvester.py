from ckan import model
from ckan.logic import get_action
from ckan.plugins import toolkit
from ckanext.harvest.model import HarvestObject
from ckanext.odsh.harvesters.base import ODSHBaseHarvester

import requests
import uuid
import traceback
import json
import logging
import datetime

log = logging.getLogger(__name__)

GROUP_MAPPING = {'kultur_freizeit_sport_tourismus': 'educ', 'gesundheit': 'heal', 'politik_wahlen': 'gove',
                 'verwaltung': 'gove', 'infrastruktur_bauen_wohnen': 'regi', 'wirtschaft_arbeit': 'econ',
                 'transport_verkehr': 'tran', 'bildung_wissenschaft': 'educ', 'bevoelkerung': 'soci',
                 'gesetze_justiz': 'just', 'geo': 'regi', 'soziales': 'soci', 'umwelt_klima': 'envi'}


class KielHarvester(ODSHBaseHarvester):
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

            source_dataset = get_action('package_show')(context.copy(), {'id': harvest_object.source.id})
            package_dict['owner_org'] = source_dataset.get('owner_org')

            if package_dict['type'] == 'datensatz':
                package_dict['type'] = 'dataset'
            package_dict['id'] = harvest_object.guid

            tags = package_dict['tags']
            package_dict['tags'] = list()
            for tag in tags:
                package_dict['tags'].append({'name': tag})

            mapped_groups = list()
            groups = package_dict['groups']
            if isinstance(groups, str):
                groups = [groups]
            for group in groups:
                if GROUP_MAPPING[group]:
                    mapped_groups.append({'name': GROUP_MAPPING[group]})
            package_dict['groups'] = mapped_groups

            published = str()
            package_dict['extras'] = list()
            for extra in package_dict['extras']:
                if extra['key'] == 'dates':
                    published = extra['value']['date']
                    package_dict['extras'].append({'key': 'issued', 'value': published})
                elif extra['key'] in ['temporal_start', 'temporal_end']:
                    package_dict['extras'].append(extra)
            for date in package_dict['extras']['dates']:
                if date['role'] == 'veroeffentlicht':
                    published = datetime.datetime.strptime(date['date'], "%d.%m.%Y").isoformat()
            package_dict['extras'].append({'key': 'issued', 'value': published})
            package_dict['extras'].append({'key': 'spatial_uri', 'value': 'http://dcat-ap.de/def/politicalGeocoding/districtKey/01002'})

            #license_id = self._get_license_id(package_dict['license_id'])
            license_id = 'http://dcat-ap.de/def/licenses/dl-zero-de/2.0'
            if license_id:
                package_dict['license_id'] = license_id
            else:
                log.error('invalid license_id: %s' % package_dict['license_id'])
                self._save_object_error('Invalid license_id: %s' % package_dict['license_id'], harvest_object, 'Import')
                return False
            try:
                result = self._create_or_update_package(package_dict, harvest_object, package_dict_form='package_show')
                return result
            except toolkit.ValidationError as e:
                self._save_object_error('Validation Error: %s' % str(e.error_summary), harvest_object, 'Import')
                return False
