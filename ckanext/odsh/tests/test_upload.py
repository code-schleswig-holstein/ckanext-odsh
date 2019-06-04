
# encoding: utf-8

import ckan.tests.factories as factories
import ckan.tests.helpers as helpers
from ckan import model
from test_helpers import odsh_test
from routes import url_for
from nose.tools import assert_true, assert_false, assert_equal, assert_in
from ckanext.odsh.helpers import odsh_create_checksum
webtest_submit = helpers.webtest_submit
import pdb


class TestUpload(helpers.FunctionalTestBase):

    _load_plugins = ['odsh', 'spatial_metadata', 'spatial_query']

    def teardown(self):
        model.repo.rebuild_db()

    @odsh_test()
    def test_upload_empty_form_fails(self):
        # arrange
        form = self._get_package_new_form()

        # act
        response = self._submit_form(form)

        # assert
        response.mustcontain('Title: Missing value')
        response.mustcontain('Description: Missing value')
        response.mustcontain('temporal_start: empty')

    @odsh_test()
    def test_upload_empty_wrong_spatial_uri(self):
        # arrange
        form = self._get_package_new_form()

        # act
        form[self._get_field_name('spatial_uri')] = 'wrong'
        response = self._submit_form(form)

        # assert
        response.mustcontain('spatial_uri: uri unknown')

    @odsh_test()
    def test_upload_empty_spatial_uri(self):
        # arrange
        form = self._get_package_new_form()

        # act
        form[self._get_field_name('spatial_uri')] = ''
        response = self._submit_form(form)

        # assert
        assert 'spatial_uri: empty not allowed' in response

    @odsh_test()
    def test_edit_empty_spatial_uri(self):
        # arrange
        dataset = self._create_dataset()

        form = self._get_package_update_form(dataset['id'])

        # act
        form[self._get_field_name('spatial_uri')] = ''
        response = self._submit_form(form)

        # assert
        assert 'spatial_uri: empty not allowed' in response

    @odsh_test()
    def test_edit_empty_spatial_uri_but_spatial(self):
        # arrange
        extras = [
            {'key': 'temporal_start', 'value': '2000-01-27'},
            {'key': 'temporal_end', 'value': '2000-01-27'},
            {'key': 'issued', 'value': '2000-01-27'},
            {'key': 'groups', 'value': 'soci'},
            {'key': 'licenseAttributionByText', 'value': 'text'},
            {'key': 'spatial_uri', 'value': ''},
            {'key': 'spatial', 'value': '{"type": "Point", "coordinates": [9.511769, 53.928028]}'},
        ]
        dataset = self._create_dataset(extras=extras)
        # pdb.set_trace()

        form = self._get_package_update_form(dataset['id'])

        # # act
        # form[self._get_field_name('spatial_uri')] = ''
        # response = self._submit_form(form)

        # # assert
        # assert 'spatial_uri: empty not allowed' not in response
        response = self._submit_and_follow_form(form)

        # assert
        response.mustcontain('Manage Dataset')
        response.mustcontain('module module-narrow dataset-map')

    @odsh_test()
    def test_edit_valid_dataset(self):
        # arrange
        dataset = self._create_dataset()

        form = self._get_package_update_form(dataset['id'])

        # # act
        # form[self._get_field_name('spatial_uri')] = ''
        # response = self._submit_form(form)

        # # assert
        # assert 'spatial_uri: empty not allowed' not in response
        response = self._submit_and_follow_form(form)

        # assert
        response.mustcontain('Manage Dataset')
        response.mustcontain('module module-narrow dataset-map')

    @odsh_test()
    def test_upload_empty_wrong_date_temporal_start(self):
        # arrange
        form = self._get_package_new_form()

        # act
        form[self._get_field_name('temporal_start')] = '2001-12-35'
        response1 = self._submit_form(form)
        form[self._get_field_name('temporal_end')] = '2001-12-35'
        response2 = self._submit_form(form)
        form[self._get_field_name('temporal_start')] = '2001-12-01'
        response3 = self._submit_form(form)
        form[self._get_field_name('temporal_end')] = '2001-12-01'
        form[self._get_field_name('temporal_start')] = '2001-12-35'
        response4 = self._submit_form(form)
        form[self._get_field_name('temporal_start')] = '11-11-11'
        response5 = self._submit_form(form)
        form[self._get_field_name('temporal_start')] = '11-11-2011'
        response6 = self._submit_form(form)
        form[self._get_field_name('temporal_start')] = 'datum'
        response7 = self._submit_form(form)

        # assert
        response1.mustcontain('temporal_start: not a valid date')
        # response2.mustcontain('odsh_temporal_error_label')
        response3.mustcontain('temporal_end: not a valid date')
        response4.mustcontain('temporal_start: not a valid date')
        response5.mustcontain('temporal_start: not a valid date')
        response6.mustcontain('temporal_start: not a valid date')

    @odsh_test()
    def test_upload_all_fields_set(self):
        # arrange
        form = self._get_package_new_form()
        form['title'] = 'Titel'
        form['notes'] = 'notes'
        form['owner_org'] = self.org['id']
        form[self._get_field_name(
            'spatial_uri')] = 'http://dcat-ap.de/def/politicalGeocoding/districtKey/01001'
        form[self._get_field_name('issued')] = '2019-01-29'
        form[self._get_field_name('temporal_start')] = '2019-01-29'
        form[self._get_field_name('groups')] = 'soci'
        form[self._get_field_name('temporal_end')] = '2019-02-02'
        form['license_id'] = 'http://dcat-ap.de/def/licenses/dl-by-de/2.0'
        form[self._get_field_name('licenseAttributionByText')].value = 'text'

        # act
        response = self._submit_and_follow_form(form)

        # assert
        assert_true('resource-edit' in response.forms)
        # map enabled

    @odsh_test()
    def test_upload_license(self):
        # arrange
        form = self._get_package_new_form()

        # act
        form['license_id'] = 'http://dcat-ap.de/def/licenses/dl-by-de/2.0'
        form[self._get_field_name('licenseAttributionByText')].value = ''
        response1 = self._submit_form(form)

        # assert
        response1.mustcontain('licenseAttributionByText: empty not allowed')

    @odsh_test()
    def test_read_dataset(self):
        # arrange
        dataset = self._create_dataset()
        resource = factories.Resource(package_id=dataset['id'],name='test_resource')

        # act
        response = self._get_package_read_page(dataset['id'])

        # assert
        response.mustcontain('Manage Dataset')
        response.mustcontain('module module-narrow dataset-map')
        response.mustcontain('<a href="http://link.to.some.data">')

    @odsh_test()
    def test_read_dataset_with_uploaded_resource(self):
        # arrange
        dataset = self._create_dataset()
        resource = factories.Resource(
            package_id=dataset['id'],
            url='http://server.com/path/download.pdf',
            url_type='upload')

        # act
        response = self._get_package_read_page(dataset['id'])

        # assert
        response.mustcontain('<a href="/dataset/{did}/resource/{rid}/download/download.pdf">'.format(did=dataset['id'], rid=resource['id']))

    def _get_field_name(self, field):
        checksum = odsh_create_checksum(field)
        return 'extras__' + str(checksum) + '__value'

    def _get_field_key(self, field):
        checksum = odsh_create_checksum(field)
        return 'extras__' + str(checksum) + '__key'

    def _submit_form(self, form):
        return webtest_submit(form, 'save', status=200, extra_environ=self.env)

    def _submit_and_follow_form(self, form):
        app = self._get_test_app()
        # return webtest_submit(form, 'save', status=200, extra_environ=self.env)
        return helpers.submit_and_follow(app, form, self.env, 'save')

    def _get_package_new_form(self):
        app = self._get_test_app()
        user = factories.User()
        self.org = factories.Organization(
            name="my-org",
            users=[{'name': user['id'], 'capacity': 'admin'}]
        )
        self.env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(
            url=url_for(controller='package', action='new'),
            extra_environ=self.env,
        )
        return response.forms['dataset-edit']

    def _get_package_update_form(self, id):
        app = self._get_test_app()
        # user = factories.User()
        response = app.get(
            url=url_for(controller='package', action='edit', id=id),
            extra_environ=self.env,
        )
        return response.forms['dataset-edit']

    def _get_package_read_page(self, id):
        app = self._get_test_app()
        # user = factories.User()
        response = app.get(
            url=url_for(controller='package', action='read', id=id),
            extra_environ=self.env,
        )
        return response

    def _create_dataset(self, name='my-own-dataset', temporal_start='2000-01-27', temporal_end='2000-01-27',title='title', extras=None):
        user = factories.User()
        self.org = factories.Organization(
            name="my-org",
            users=[{'name': user['id'], 'capacity': 'admin'}]
        )
        self.env = {'REMOTE_USER': user['name'].encode('ascii')}
        if not extras:
            extras = [
                {'key': 'temporal_start', 'value': temporal_start},
                {'key': 'temporal_end', 'value': temporal_end},
                {'key': 'issued', 'value': '2000-01-27'},
                {'key': 'spatial_uri', 'value': 'http://dcat-ap.de/def/politicalGeocoding/districtKey/01001'},
                {'key': 'groups', 'value': 'soci'},
                {'key': 'licenseAttributionByText', 'value': 'text'}
            ]
        dataset = factories.Dataset(user=user,
                                 name=name,
                                 title=title,
                                 issued='27-01-2000',
                                 extras=extras,
                                 license_id='http://dcat-ap.de/def/licenses/dl-by-de/2.0')
        return dataset

