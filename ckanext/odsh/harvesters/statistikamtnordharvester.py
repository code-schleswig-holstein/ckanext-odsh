# This Python file uses the following encoding: utf-8

import json
import urllib2
import traceback

from lxml import etree
from ckan import model

from ckan.logic import get_action
import ckan.lib.plugins as lib_plugins
from ckan.plugins import toolkit
import datetime

from ckanext.harvest.model import HarvestObject
from ckanext.odsh.harvesters.base import ODSHBaseHarvester

from ckanext.odsh.model.statistiknord import *
import logging

log = logging.getLogger(__name__)


class StatistikamtNordHarvester(ODSHBaseHarvester):
    """
    A Harvester for Statistikamt Nord
    """

    @staticmethod
    def info():
        return {
            'name': 'statistikamt-nord',
            'title': 'Statistikamt Nord',
            'description': 'Harvests Statistikamt Nord',
            'form_config_interface': 'Text'
        }

    def gather_stage(self, harvest_job):
        url = harvest_job.source.url

        try:
            log.info('Stat_Nord_Harvester: Beginning gather stage')
            fetched_documents = self._get_content(url)
            documents_list = self.get_documents_from_content(fetched_documents)
            documents = documents_list['RegistereintragsListe']

        except Exception, e:
            log.error('traceback while reading model: %s' % traceback.format_exc())
            self._save_gather_error('Statistik-Nord-Harvester: Error while reading model [%r]' % e, harvest_job)
            return False

        try:
            used_identifiers = []
            ids = []
            package_ids_in_db = list(map(lambda x: x[0], model.Session.query(HarvestObject.guid) \
                                         .filter(HarvestObject.current == True) \
                                         .filter(HarvestObject.harvest_source_id == harvest_job.source.id).all()))
            log.info("Package IDs in DB: %s" % str(package_ids_in_db))
            for document in documents:
                try:
                    fetched_values = self.get_values_from_content(document)
                    identifier = self._create_inforeg_id(fetched_values)

                    if identifier in used_identifiers:
                        log.error("ID: already known - gather process failed ")
                        continue

                    if identifier is None:
                        log.error("ID: unknown - gather process failed ")
                        continue

                    if identifier not in package_ids_in_db:
                        obj = HarvestObject(guid=identifier,
                                            job=harvest_job)
                        obj.content = json.dumps(fetched_values)
                        obj.save()
                        log.info(
                            "harvest_object_id: %s, GUID: %s successfully gathered " % (str(obj.id), str(obj.guid)))
                        used_identifiers.append(identifier)
                        ids.append(obj.id)
                        log.debug('Save identifier %s from Statistik Nord' % identifier)

                except Exception, e:
                    log.error('traceback: %s' % traceback.format_exc())
                    self._save_gather_error(
                        'Statistik-Nord-Harvester: Error for the identifier %s [%r]' % (identifier, e), harvest_job)
                    continue

        except Exception, e:
            self._save_gather_error(
                'Statistik-Nord-Harvester: Error gathering the identifiers from the source server [%s]' % str(e),
                harvest_job)
            log.error(e)
            return None

        if len(ids) > 0:
            log.info("finished %s IDs of %s IDs successfully gathered" % (len(used_identifiers), len(documents)))
            log.debug("gather_stage() finished: %s IDs gathered" % len(ids))
            return ids
        else:
            log.error("No records received")
            self._save_gather_error("Couldn't find any metadata files", harvest_job)
            return None

    @staticmethod
    def fetch_stage(harvest_object):
        return True

    def import_stage(self, harvest_object):
        context = {
            'model': model,
            'session': model.Session,
            'user': self._get_user_name(),
        }
        log.debug("Context: " + str(context.viewitems()))
        if not harvest_object:
            log.error('Statistik-Nord-Harvester: No harvest object received')
            return False

        if harvest_object.content is None:
            self._save_object_error('Empty content for object %s' % harvest_object.id, harvest_object, u'Import')
            return False
        else:
            log.debug("Harvest Object: " + str(harvest_object))
            self.map_fields(context, harvest_object)
            return True

    @staticmethod
    def _update_schema(schema):
        schema.update({'temporal_start': [
            toolkit.get_validator('ignore_empty'),
            toolkit.get_converter('convert_to_extras')]})
        schema.update({'temporal_end': [
            toolkit.get_validator('ignore_empty'),
            toolkit.get_converter('convert_to_extras')]})

    def map_fields(self, context, harvest_object):
        values = json.loads(harvest_object.content)

        package_dict = dict()
        package_dict.update({'resources': [], 'tags': [], 'groups': []})
        title = values['Titel']
        package_dict.update({'title': title})
        package_dict.update({'name': self._gen_new_name(title)})
        # Beschreibung sollte noch geliefert werden!
        package_dict.update({'notes': values['Beschreibung'] or values['Ressourcen']['Ressource'][0]['Ressourcenname']})
        package_dict.update({'license_id': self._get_license_id(values['Nutzungsbestimmungen']['ID_derLizenz'][0])})
        package_dict.update({'author': values["VeroeffentlichendeStelle"]["Name"]})
        package_dict.update({'author_email': values["VeroeffentlichendeStelle"]["EMailAdresse"]})

        if values['Ansprechpartner']:
            package_dict.update({'maintainer': values['Ansprechpartner']['Name'],
                                 'maintainer_email': values['Ansprechpartner']['EMailAdresse']})
        try:
            package_dict['url'] = values['WeitereInformationen']['URL']
        except KeyError:
            package_dict['url'] = ""
        package_dict.update({'type': 'dataset'})

        package_dict.update({'licenseAttributionByText': 'Statistisches Amt für Hamburg und Schleswig-Holstein -'
                                                         ' Anstalt des öffentlichen Rechts - (Statistikamt Nord)'})
        package_dict.update({'temporal_start': values['ZeitraumVon']})
        package_dict.update({'temporal_end': values['ZeitraumBis']})
        package_dict.update({'spatial_uri': 'http://dcat-ap.de/def/politicalGeocoding/stateKey/01'})
        # issued sollte noch geliefert werden!
        package_dict.update({'issued': datetime.datetime.now()})
        self.add_ressources(package_dict, values)

        self.add_tags(package_dict, values)

        self.map_to_group(package_dict, values)

        source_dataset = get_action('package_show')(context.copy(), {'id': harvest_object.source.id})

        package_dict['owner_org'] = source_dataset.get('owner_org')

        package_dict['id'] = harvest_object.guid

        try:
            context = {'user': self._get_user_name(), 'return_id_only': True, 'ignore_auth': True}
            package_plugin = lib_plugins.lookup_package_plugin(package_dict.get('type', None))
            package_schema = package_plugin.create_package_schema()
            self._update_schema(package_schema)
            context['schema'] = package_schema
            self._handle_current_harvest_object(harvest_object, harvest_object.guid)
            result = toolkit.get_action('package_create')(context, package_dict)
            return result
        except toolkit.ValidationError, e:
            self._save_object_error('Validation Error: %s' % str(e.error_summary), harvest_object, 'Import')
            return False

    @staticmethod
    def add_tags(package_dict, values):
        tags = values['Schlagwoerter']['Schlagwort']
        for tag in tags:
            seperated_tags = tag.split(',')
            for seperated_tag in seperated_tags:
                if seperated_tag != '' and len(seperated_tag) < 100:
                    package_dict['tags'].append({'name': seperated_tag.strip()})

    @staticmethod
    def add_ressources(package_dict, values):
        resources = values['Ressourcen']['Ressource']
        for resource in resources:
            resource_dict = dict()
            resource_dict['name'] = resource['Ressourcenname']
            resource_dict['format'] = resource['Format'].get('FormatTyp', "")
            resource_dict['url'] = resource['URLZumDownload']
            if resource['Dateigroesse'] == "0" or len(resource['Dateigroesse']) == 0:
                resource_file = urllib2.urlopen(resource['url'])
                resource_dict['file_size'] = resource_file['Content-Length']
            else:
                file_size = int(round(float(resource['Dateigroesse']) * 1000000000))
                resource_dict['size'] = file_size
            package_dict['resources'].append(resource_dict)

    @staticmethod
    def map_to_group(package_dict, values):
        # open file with the mapping from numbers to DCAT-DE vocabulary:
        # TODO: needs to be set in the ckan config file, not hardcoded
        with open('/usr/lib/ckan/default/src/ckanext-odsh/ckanext/odsh/harvesters/number_dcat_de_hamburg.json') as f:
            dcat_theme = json.load(f)
        # get the code
        code = values['StANKategorie']

        if dcat_theme.has_key(str(code)):
                for item in dcat_theme[str(code)]:
                    package_dict['groups'].append({'name': item})
        else:
            log.error('Statistik-Nord-Harvester: No valid group code received: %s', code)

    @staticmethod
    def _get_content(url):
        url = url.replace(' ', '%20')
        try:
            http_response = urllib2.urlopen(url, timeout=100000)
            content = http_response.read()
            return content
        except Exception, e:
            log.error('traceback WebHarvester could not get content!: %s' % traceback.format_exc())
            log.debug("Error in _get_content %s" % e)
            raise e

    @staticmethod
    def get_documents_from_content(content):
        fetched_xml = etree.fromstring(content)
        fetched_string = etree.tostring(fetched_xml)

        fetched_document = StatistikNordDocuments(fetched_string)

        fetched_values = fetched_document.read_values()
        return fetched_values

    @staticmethod
    def get_values_from_content(content):
        fetched_xml = etree.fromstring(content)
        fetched_string = etree.tostring(fetched_xml)
        fetched_document = StatistikNordDocument(fetched_string)
        fetched_values = fetched_document.read_values()

        return fetched_values

    @staticmethod
    def _create_inforeg_id(values):
        guid = values['DokumentID']
        quelle = values['Quelle']
        if guid.startswith(quelle):
            return guid.strip()
        else:
            return quelle + ':' + guid.strip()



    @staticmethod
    def get_all_groups():
        result_groups = []
        groups_in_database = model.Session.query(model.Group.name).filter(model.Group.state == 'active')
        for group_in_database in groups_in_database.all():
            result_groups.append(group_in_database.name)

        return result_groups


class ContentFetchError(Exception):
    pass


class ContentNotFoundError(ContentFetchError):
    pass


class RemoteResourceError(Exception):
    pass


class SearchError(Exception):
    pass
