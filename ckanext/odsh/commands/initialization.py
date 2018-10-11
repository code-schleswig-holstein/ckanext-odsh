#!/usr/bin/env python
# -*- coding: utf8 -*-
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
            "kiel": "Kiel",
            "statistikamt-nord": "Statistikamt Nord"
        }

        for org_key in odsh_orgs:
            if org_key not in present_orgs_keys:
                add_message = 'Adding group {org_key}.'.format(
                    org_key=org_key
                )
                print(add_message)
                group_dict = {
                    'name': org_key,
                    'id': org_key,
                    'title': odsh_orgs[org_key]
                }

                self._create_and_purge_organization(
                    group_dict
                )
            else:
                skip_message = 'Skipping creation of organization '
                skip_message = skip_message + "{org_key}, as it's already present."
                print(skip_message.format(org_key=org_key))

    def _handle_harvesters(self, ckan_api_client):
        data_dict = {}
        harvesters = get_action('harvest_source_list')(self.create_context_with_user(), data_dict)
        present_harvesters_list = list()
        for harvester in harvesters:
            present_harvesters_list.append(harvester["title"])

        odsh_harvesters = {
            "Kiel": {
                'name': "kiel",
                'url': "https://www.kiel.de/de/kiel_zukunft/statistik_kieler_zahlen/open_data/Kiel_open_data.json",
                'source_type': "kiel",
                'title': "Kiel",
                'active': True,
                'owner_org': "kiel",
                'frequency': "MANUAL"
            },
            "Statistikamt Nord": {
                'name': "statistikamt-nord",
                'url': "http://www.statistik-nord.de/index.php?eID=stan_xml&products=4,6&state=2",
                'source_type': "statistikamt-nord",
                'title': "Statistikamt Nord",
                'active': True,
                'owner_org': "statistikamt-nord",
                'frequency': "MANUAL"
            }
        }

        for harvester_key in odsh_harvesters:
            if harvester_key not in present_harvesters_list:
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
