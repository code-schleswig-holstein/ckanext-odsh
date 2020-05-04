from ckan import model
from ckan.logic import get_action
from ckan.plugins import toolkit
import ckan.lib.plugins as lib_plugins
from ckanext.harvest.model import HarvestObject
from ckanext.odsh.harvesters.base import ODSHBaseHarvester

import requests
import uuid
import json
import logging

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
        count_known_dataset_ids = 0

        try:
            used_identifiers = []
            ids = []
            package_ids_in_db = list(map(lambda x: x[0], model.Session.query(HarvestObject.guid)
                                .filter(HarvestObject.current == True)
                                .filter(HarvestObject.harvest_source_id == harvest_job.source.id).all()))
            log.info("Package IDs in DB: %s" % str(package_ids_in_db))
            for dataset in datasets:
                guid = str(uuid.uuid3(uuid.NAMESPACE_URL,
                           dataset.get("url").encode('ascii', 'ignore')))
                if guid not in package_ids_in_db:
                    obj = HarvestObject(job=harvest_job, guid=guid)
                    obj.content = json.dumps(dataset)
                    obj.save()
                    log.info("harvest_object_id: %s, GUID: %s successfully gathered " % (
                        str(obj.id), str(obj.guid)))
                    used_identifiers.append(guid)
                    ids.append(obj.id)
                else:
                    count_known_dataset_ids += 1

        except Exception as e:
            self._save_gather_error(
                'Kiel-Harvester: Error gathering the identifiers from the source server [%s]' % str(
                    e),
                harvest_job)
            log.error(e)
            return None

        if len(ids) > 0:
            log.info(
                "finished %s IDs of %s IDs successfully gathered" % (len(used_identifiers), len(datasets)))
            log.debug("List of gathered IDs: %s" % ids)
            log.debug("gather_stage() finished: %s IDs gathered" % len(ids))
            return ids
        elif count_known_dataset_ids > 0:
            log.info("Gathered " + str(count_known_dataset_ids) + 
              " datasets already stored in the database. No new datasets found.")
            return []
        else:
            log.error("No records received")
            self._save_gather_error(
                "Couldn't find any metadata files", harvest_job)
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
            'return_id_only': True,
            'ignore_auth': True
        }
        if not harvest_object:
            log.error('Kiel-Harvester: No harvest object received')
            return False

        if harvest_object.content is None:
            self._save_object_error(
                'Empty content for object %s' % harvest_object.id, harvest_object, 'Import')
            return False
        else:
            package_dict = json.loads(harvest_object.content)

            source_dataset = get_action('package_show')(
                context.copy(), {'id': harvest_object.source.id})
            package_dict['owner_org'] = source_dataset.get('owner_org')

            if package_dict['type'] in ('datensatz', 'dokument', 'document'):
                package_dict['type'] = 'dataset'
            package_dict['id'] = harvest_object.guid

            tags = package_dict['tags']
            package_dict['tags'] = list()
            for tag in tags:
                package_dict['tags'].append({'name': tag})

            mapped_groups = list()
            groups = package_dict['groups']

            for group in groups:
                if GROUP_MAPPING[group]:
                    mapped_groups.append({'name': GROUP_MAPPING[group]})
            package_dict['groups'] = mapped_groups

            extras = package_dict['extras']
            new_extras = list()
            for extra in extras:
                # WARNING: When this code was written, all datasets had '-zero-' licences, i.e.
                # there was no key 'licenseAttributionByText' which we would expect for '-by-' licences.
                # The setting is just anticipated, matching for datasets with a corresponding licence.
                if extra['key'] == 'licenseAttributionByText':
                    new_extras.append(extra)
                elif extra['key'] in ['temporal_start', 'temporal_end', 'issued']:
                    new_extras.append(extra)

            new_extras.append(
                {'key': 'spatial_uri',
                 'value': 'http://dcat-ap.de/def/politicalGeocoding/districtKey/01002'})

            package_dict['extras'] = new_extras

            license_id = self._get_license_id(package_dict['license_id'])
            if license_id:
                package_dict['license_id'] = license_id
            else:
                log.error('invalid license_id: %s' %
                          package_dict['license_id'])
                self._save_object_error(
                    'Invalid license_id: %s' % package_dict['license_id'], harvest_object, 'Import')
                return False
            try:
                context = {'user': self._get_user_name(
                ), 'return_id_only': True, 'ignore_auth': True}
                package_plugin = lib_plugins.lookup_package_plugin(
                    package_dict.get('type', None))
                package_schema = package_plugin.create_package_schema()
                context['schema'] = package_schema
                self._handle_current_harvest_object(harvest_object, harvest_object.guid)
                result = toolkit.get_action('package_create')(context, package_dict)
                return result
            except toolkit.ValidationError as e:
                self._save_object_error('Validation Error: %s' % str(e.error_summary), harvest_object, 'Import')
                return False
