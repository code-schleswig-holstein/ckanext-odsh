
# encoding: utf-8

import ckan.tests.factories as factories
import ckan.tests.helpers as helpers
from ckan import model
from test_helpers import odsh_test
from routes import url_for
from nose.tools import assert_true, assert_false, assert_equal, assert_in
from ckanext.odsh.helpers import odsh_create_checksum
webtest_submit = helpers.webtest_submit


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
        response.mustcontain('odsh_spatial_uri_error_label')
        response.mustcontain('odsh_temporal_error_label')

    @odsh_test()
    def test_upload_empty_wrong_spatial_uri(self):
        # arrange
        form = self._get_package_new_form()

        # act
        form[self._get_field_name('spatial_uri')]='wrong'
        response = self._submit_form(form)

        # assert
        response.mustcontain('odsh_spatial_uri_unknown_error_label')

    @odsh_test()
    def test_upload_empty_wrong_date_temporal_start(self):
        # arrange
        form = self._get_package_new_form()

        # act
        form[self._get_field_name('temporal_start')]='2001-12-35'
        response1 = self._submit_form(form)
        form[self._get_field_name('temporal_end')]='2001-12-35'
        response2 = self._submit_form(form)
        form[self._get_field_name('temporal_start')]='2001-12-01'
        response3 = self._submit_form(form)
        form[self._get_field_name('temporal_end')]='2001-12-01'
        form[self._get_field_name('temporal_start')]='2001-12-35'
        response4 = self._submit_form(form)
        form[self._get_field_name('temporal_start')]='11-11-11'
        response5 = self._submit_form(form)
        form[self._get_field_name('temporal_start')]='11-11-2011'
        response6 = self._submit_form(form)
        form[self._get_field_name('temporal_start')]='datum'
        response7 = self._submit_form(form)

        # assert
        response1.mustcontain('odsh_temporal_error_label')
        response2.mustcontain('odsh_temporal_error_label')
        response3.mustcontain('odsh_temporal_end_not_date_error_label')
        response4.mustcontain('odsh_temporal_start_not_date_error_label')
        response5.mustcontain('odsh_temporal_start_not_date_error_label')
        response6.mustcontain('odsh_temporal_start_not_date_error_label')


    def _get_field_name(self, field):
        checksum = odsh_create_checksum(field)
        return 'extras__' + str(checksum) + '__value'

    def _submit_form(self, form):
        return webtest_submit(form, 'save', status=200, extra_environ=self.env)

    def _get_package_new_form(self):
        app = self._get_test_app()
        user = factories.User()
        self.env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(
            url=url_for(controller='package', action='new'),
            extra_environ=self.env,
        )
        return response.forms['dataset-edit']