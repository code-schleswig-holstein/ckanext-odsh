import urllib2
import traceback

from ckanext.odsh.harvesters.ckan_mapper import pyjq_mapper
from lxml import etree
import uuid

from ckan import model
from ckan.logic import get_action
from ckan.lib.helpers import json

from ckan.plugins import toolkit

from ckanext.harvest.model import HarvestObject
from ckanext.harvest.harvesters.base import HarvesterBase

from ckanext.odsh.model.statistiknord import *
import logging

log = logging.getLogger(__name__)


class StatistikNordHarvester(HarvesterBase):
    '''
    A Harvester for Statistikamt Nord
    '''

    def info(self):
        return {
            'name': 'statistik-nord',
            'title': 'Statistik Nord',
            'description': 'Harvests Statistikamt Nord',
            'form_config_interface': 'Text'
        }

    def gather_stage(self, harvest_job):
        url = harvest_job.source.url

        try:
            fetched_documents = self._get_content(url)
            documents_list = self.get_documents_from_content(fetched_documents)
            documents = documents_list['RegistereintragsListe']
        except Exception, e:
            #log.error('traceback while reading model: %s' % traceback.format_exc())
            self._save_gather_error('Statistik-Nord-Harvester: Error while reading model [%r]' % e, harvest_job)
            return False

        try:
            used_identifiers = []
            ids = []
            for document in documents:
                try:
                    fetched_values = self.get_values_from_content(document)
                    identifier = self._create_inforeg_id(fetched_values)
                    #log.info('identifier: %s' % identifier)

                    if identifier in used_identifiers:
                        continue

                    if identifier is None:
                        log.error("ID: unknown - gather process failed ")
                        continue

                    if identifier:
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
            #log.info(
            #    "finished %s IDs of %s IDs successfully gathered" % (len(used_identifiers), len(documents)))
            #log.debug("List of gathered IDs: %s" % ids)
            #log.debug("gather_stage() finished: %s IDs gathered" % len(ids))
            return ids
        else:
            #log.error("No records received")
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
        #log.debug("user: " + self._get_user_name())
        if not harvest_object:
            log.error('Statistik-Nord-Harvester: No harvest object received')
            return False

        if harvest_object.content is None:
            self._save_object_error('Empty content for object %s' % harvest_object.id, harvest_object, u'Import')
            return False
        else:
            self.use_mapper(context, harvest_object)
            #self.original_method(context, harvest_object)

            return True

    def use_mapper(self, context, harvest_object):
        values = json.loads(harvest_object.content)
        package = dict()

        package = pyjq_mapper(values)
        source_dataset = get_action('package_show')(context.copy(), {'id': harvest_object.source.id})
        package['owner_org'] = source_dataset.get('owner_org')
        package['id'] = str(uuid.uuid4())

        package_dict = dict(package)
        log.debug("license_id: " + str(package_dict["license_id"]))
        log.debug("extras: " + str(package_dict["extras"]))
        if package_dict.has_key("maintainer"):
            log.debug("maintainer: " + str(package_dict["maintainer"]))
        log.debug("url: " + str(package_dict["url"]))
        log.debug("resources/file_size: " + str(package_dict["resources"]))
        log.debug("tags: " + str(package_dict["tags"]))

        try:
            result = self._create_or_update_package(package_dict, harvest_object, package_dict_form='package_show')
            return result
        except toolkit.ValidationError, e:
            self._save_object_error('Validation Error: %s' % str(e.error_summary), harvest_object, 'Import')
            return False

    def original_method(self, context, harvest_object):
        values = json.loads(harvest_object.content)
        #log.debug(values)
        package_dict = dict()
        package_dict.update({'resources': [], 'tags': [], 'groups': []})
        package_dict.update({'title': values['Titel']})
        package_dict.update({'notes': values['Beschreibung']})
        package_dict.update({'license_id': values['Nutzungsbestimmungen']['ID_derLizenz'][0]})
        package_dict.update({'author': values["VeroeffentlichendeStelle"]["Name"]})
        package_dict.update({'author_email': values["VeroeffentlichendeStelle"]["EMailAdresse"]})
        extras = list()
        extras.append({'key': 'identifier', 'value': self._create_inforeg_id(values)})
        package_dict['extras'] = extras
        if values['Ansprechpartner']:
            package_dict.update({'maintainer': values['Ansprechpartner']['Name'],
                                 'maintainer_email': values['Ansprechpartner']['EMailAdresse']})
        try:
            package_dict['url'] = values['WeitereInformationen']['URL']
        except KeyError:
            package_dict['url'] = ""
        package_dict.update({'type': 'dataset'})
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
                file_size = int(round(float(resource['Dateigroesse']) * 1000000))
                resource_dict['file_size'] = file_size
            package_dict['resources'].append(resource_dict)
        tags = values['Schlagwoerter']['Schlagwort']
        #
        for tag in tags:
            seperated_tags = tag.split(',')
            for seperated_tag in seperated_tags:
                if seperated_tag != '' and len(seperated_tag) < 100:
                    package_dict['tags'].append({'name': seperated_tag.strip()})

        self.map_to_group(package_dict, values)
        ## How To?:
        source_dataset = get_action('package_show')(context.copy(), {'id': harvest_object.source.id})
        package_dict['owner_org'] = source_dataset.get('owner_org')
        package_dict['id'] = str(uuid.uuid4())
        log.debug("license_id: " + str(package_dict["license_id"]))
        log.debug("extras: " + str(package_dict["extras"]))
        if package_dict.has_key("maintainer"):
            log.debug("maintainer: " + str(package_dict["maintainer"]))
        log.debug("url: " + str(package_dict["url"]))
        log.debug("resource/file_size: " + str(package_dict["resources"]))
        log.debug("tags: " + str(package_dict["tags"]))

        try:
            result = self._create_or_update_package(package_dict, harvest_object, package_dict_form='package_show')
            return result
        except toolkit.ValidationError, e:
            self._save_object_error('Validation Error: %s' % str(e.error_summary), harvest_object, 'Import')
            return False

    def map_to_group(self, package_dict, values):
        # open file with the mapping from numbers to DCAT-DE vocabulary:
        with open('/usr/lib/ckan/default/src/ckanext-odsh/ckanext/odsh/harvesters/number_dcat_de.json') as f:
            dcat_theme = json.load(f)
        # get the code
        code = values['StANKategorie']
        # if possible map it to a group
        if dcat_theme.has_key(str(code)):
            for item in dcat_theme[str(code)]:
                package_dict['groups'].append({'name': item})
                #log.debug("DEBUG: DCAT-DE Code Mapping from %s to %s", str(code), item)

    @staticmethod
    def _get_content(url):
        url = url.replace(' ', '%20')
        #log.debug("get_content StatistikNord harvester: %s" % url)
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

    def add_groups_to_fetched_values(self, fetched_values):
        groups = []
        if 'StANProdukte' in fetched_values and '4' in fetched_values['StANProdukte']:
            #log.debug("Get Groups from database")
            groups = self.get_all_groups()
        #else:
         #   if 'StANThemen' in fetched_values:
          #      groups = self.translate_group(fetched_values['StANThemen'])

        fetched_values['Kategorie'] = {}
        fetched_values['Kategorie']['NameDerKategorie'] = []
        if groups:
            fetched_values['Kategorie']['NameDerKategorie'] = groups

        #log.debug(fetched_values['Kategorie']['NameDerKategorie'])
        return fetched_values

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
