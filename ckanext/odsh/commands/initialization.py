#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Paster command for adding ODSH organizations and harvesters to the CKAN instance.
"""
import sys
from ckan import model
from ckan.lib.cli import CkanCommand
from ckan.logic import NotFound, get_action
import ckanapi


class Initialization(CkanCommand):
    """
    Adds a default set of organizations and harvesters to the current CKAN instance.

    Usage: odsh_initialization
    """

    summary = __doc__.split('\n')[0]
    usage = __doc__

    def __init__(self, name):
        super(Initialization, self).__init__(name)
        self.admin_user = None

    def create_context_with_user(self):
        if not self.admin_user:
            # Getting/Setting default site user
            context = {'model': model, 'session': model.Session, 'ignore_auth': True}
            self.admin_user = get_action('get_site_user')(context, {})

        return {'user': self.admin_user['name']}

    def command(self):
        """Worker command doing the actual organization/harvester additions."""

        if len(self.args) > 0:
            cmd = self.args[0]

            print('Command %s not recognized' % cmd)
            self.parser.print_usage()
            sys.exit(1)

        super(Initialization, self)._load_config()
        ckan_api_client = ckanapi.LocalCKAN()

        self._handle_organizations(ckan_api_client)
        self._handle_harvesters(ckan_api_client)

    def _handle_organizations(self, ckan_api_client):
        present_orgs_dict = ckan_api_client.action.organization_list()

        present_orgs_keys = []
        if len(present_orgs_dict) > 0:
            for org_key in present_orgs_dict:
                present_orgs_keys.append(org_key)

        odsh_orgs = {
            "landeshauptstadt-kiel": {
                "title": u"Landeshauptstadt Kiel",
                "image": u"https://www.kiel.de/images/logo-kiel-sailing-city.svg",
                "description": u"Die Stadt Kiel ist die nördlichste Großstadt Deutschlands und die Landeshauptstadt"
                               u" Schleswig-Holsteins. Als kreisfreie Stadt erledigt sie neben den kommunalen"
                               u" Selbstverwaltungsaufgaben auch Aufgaben einer unteren staatlichen Verwaltungsbehörde"
                               u" und erzeugt, erhebt und verarbeitet als Gebietskörperschaft eine Vielzahl von Daten"
                               u" mit lokalem Bezug."
            },
            "statistikamt-nord": {
                "title": u"Statistisches Amt für Hamburg und Schleswig-Holstein - Anstalt des öffentlichen Rechts - "
                         u"(Statistikamt Nord)",
                "image": u"https://www.statistik-nord.de/static/img/logo-text.svg",
                "description": u"Das Statistische Amt für Hamburg und Schleswig-Holstein – das Statistikamt Nord – "
                               u"erhebt und veröffentlicht als Teil der amtlichen Statistik in Deutschland statistische"
                               u" Informationen zu allen gesellschaftlichen Themen für die Bundesländer Hamburg und"
                               u" Schleswig-Holstein. Als Anstalt des öffentlichen Rechts führt es alle durch Bundes-"
                               u" und EU- Gesetze angeordneten Statistiken im Auftrag der Trägerländer Hamburg und"
                               u" Schleswig-Holstein für die beiden Bundesländer durch, bereitet die Daten auf und"
                               u" interpretiert die Ergebnisse. Die objektiv und unabhängig erstellten Statistiken"
                               u" werden Verwaltung, Politik, Medien sowie Bürgerinnen und Bürgern gleichermaßen"
                               u" zugänglich gemacht. Darüber hinaus bietet das Amt Dienstleistungen im Bereich"
                               u" Datenerhebung, -aufbereitung und -analyse nach individuellem Kundenwunsch an."
                               u" Das Statistikamt Nord ist hervorgegangen aus den vormaligen Statistischen"
                               u" Landesämtern Hamburg und Schleswig-Holstein. Seit 2004 firmiert es als"
                               u" länderübergreifende Anstalt an den Standorten Hamburg und Kiel."
            },
            "landesamt-fur-soziale-dienste": {
                "title": u"Landesamt für soziale Dienste",
                "image": None,
                "description": u"Das Landesamt für soziale Dienste ist eine obere Landesbehörde des Landes"
                               u" Schleswig-Holstein."
            }
        }

        for org_key in odsh_orgs:
            title = odsh_orgs[org_key]['title']
            if org_key not in present_orgs_keys:
                add_message = 'Adding organization {org_title}.'.format(
                    org_title=title.encode('utf8')
                )
                print(add_message)
                group_dict = {
                    'name': org_key,
                    'id': org_key,
                    'title': title,
                    'image_url': odsh_orgs[org_key].get('image'),
                    'description': odsh_orgs[org_key].get('description')
                }

                self._create_and_purge_organization(
                    group_dict
                )
            else:
                skip_message = 'Skipping creation of organization '
                skip_message = skip_message + "{org_title}, as it's already present."
                print(skip_message.format(org_title=title.encode('utf8')))

    def _handle_harvesters(self, ckan_api_client):
        data_dict = {}
        harvesters = get_action('harvest_source_list')(self.create_context_with_user(), data_dict)
        present_harvesters_list = list()
        for harvester in harvesters:
            present_harvesters_list.append(harvester["title"])

        odsh_harvesters = {
            "Landeshauptstadt Kiel": {
                'name': u"landeshauptstadt-kiel",
                'url': u"https://www.kiel.de/de/kiel_zukunft/statistik_kieler_zahlen/open_data/Kiel_open_data.json",
                'source_type': u"kiel",
                'title': "Landeshauptstadt Kiel",
                'active': True,
                'owner_org': "landeshauptstadt-kiel",
                'frequency': "MANUAL",
                'notes': u"Die Stadt Kiel ist die nördlichste Großstadt Deutschlands und die Landeshauptstadt"
                         u" Schleswig-Holsteins. Als kreisfreie Stadt erledigt sie neben den kommunalen"
                         u" Selbstverwaltungsaufgaben auch Aufgaben einer unteren staatlichen Verwaltungsbehörde und"
                         u" erzeugt, erhebt und verarbeitet als Gebietskörperschaft eine Vielzahl von Daten mit lokalem"
                         u" Bezug."
            },
            "Statistisches Amt für Hamburg und Schleswig-Holstein - Anstalt des öffentlichen Rechts - "
            "(Statistikamt Nord)": {
                'name': u"statistikamt-nord",
                'url': u"http://www.statistik-nord.de/index.php?eID=stan_xml&products=4,6&state=2",
                'source_type': u"statistikamt-nord",
                'title': u"Statistisches Amt für Hamburg und Schleswig-Holstein - Anstalt des öffentlichen Rechts - "
                         u"(Statistikamt Nord)",
                'active': True,
                'owner_org': "statistikamt-nord",
                'frequency': "MANUAL",
                'notes': u"Das Statistische Amt für Hamburg und Schleswig-Holstein – das Statistikamt Nord – erhebt und"
                         u" veröffentlicht als Teil der amtlichen Statistik in Deutschland statistische Informationen"
                         u" zu allen gesellschaftlichen Themen für die Bundesländer Hamburg und Schleswig-Holstein. Als"
                         u" Anstalt des öffentlichen Rechts führt es alle durch Bundes- und EU- Gesetze angeordneten "
                         u"Statistiken im Auftrag der Trägerländer Hamburg und Schleswig-Holstein für die beiden "
                         u"Bundesländer durch, bereitet die Daten auf und interpretiert die Ergebnisse. Die objektiv "
                         u"und unabhängig erstellten Statistiken werden Verwaltung, Politik, Medien sowie Bürgerinnen "
                         u"und Bürgern gleichermaßen zugänglich gemacht. Darüber hinaus bietet das Amt Dienstleistungen"
                         u" im Bereich Datenerhebung, -aufbereitung und -analyse nach individuellem Kundenwunsch an. "
                         u"Das Statistikamt Nord ist hervorgegangen aus den vormaligen Statistischen Landesämtern "
                         u"Hamburg und Schleswig-Holstein. Seit 2004 firmiert es als länderübergreifende Anstalt an den"
                         u" Standorten Hamburg und Kiel."
            }
        }

        for harvester_key in odsh_harvesters:
            if unicode(harvester_key, "utf-8") not in present_harvesters_list:
                add_message = 'Adding harvester {harvester_key}.'.format(
                    harvester_key=harvester_key
                )
                print(add_message)
                harvester_dict = odsh_harvesters[harvester_key]

                get_action('harvest_source_create')(self.create_context_with_user(), harvester_dict)
            else:
                skip_message = 'Skipping creation of harvester '
                skip_message = skip_message + "{harvester_key}, as it's already present."
                print(skip_message.format(harvester_key=harvester_key))

    def _create_and_purge_organization(self, organization_dict):
        """Worker method for the actual organization addition.
        For unpurged organizations a purge happens prior."""

        try:
            get_action('organization_purge')(self.create_context_with_user(), organization_dict)
        except NotFound:
            not_found_message = 'Organization {organization_name} not found, nothing to purge.'.format(
                organization_name=organization_dict['name']
            )
            print(not_found_message)
        finally:
            get_action('organization_create')(self.create_context_with_user(), organization_dict)
