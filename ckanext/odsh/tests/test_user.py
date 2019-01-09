
# encoding: utf-8

import ckan.tests.factories as factories
import ckan.tests.helpers as helpers
from ckan import model
from test_helpers import odsh_test
from routes import url_for
from nose.tools import assert_true, assert_false, assert_equal, assert_in


class TestUser(helpers.FunctionalTestBase):

    _load_plugins = ['odsh', 'spatial_metadata', 'spatial_query']

    def teardown(self):
        model.repo.rebuild_db()

    @odsh_test()
    def test_user_login(self):
        # arrange
        user = factories.User()

        # act
        response = self._login_user(user)

        # arrange
        # we land on the default search page
        response.mustcontain('Logout')
        response.mustcontain('Search dataset')

    @odsh_test()
    def test_user_logout(self):
        #act
        final_response = self._logout()

        # assert
        assert_true('You are now logged out.' in final_response)

    @odsh_test()
    def test_user_can_see_api_key(self):
        # arrange
        user = factories.User()
        self._login_user(user)

        # act
        response = self._open_url('/user/'+user['name'])

        # assert
        # we land on the default search page
        response.mustcontain('API Key')

    @odsh_test()
    def test_user_login_wrong_password(self):
        # arrange
        user = factories.User()

        # act
        response = self._login_user(user, 'wrong')

        # assert
        response.mustcontain('Login failed. Bad username or password.')

    def _open_url(self, url):
        app = self._get_test_app()
        return app.get(url)

    def _submit_form(self, form):
        submit_response = form.submit()
        # let's go to the last redirect in the chain
        return helpers.webtest_maybe_follow(submit_response)

    def _login_user(self, user, password=None):
        response = self._open_url('/user/login')
        login_form = response.forms[0]

        login_form['login'] = user['name']
        if password is None:
            password = 'pass'
        login_form['password'] = password

        return self._submit_form(login_form)

    def _logout(self):
        app = self._get_test_app()

        logout_url = url_for(controller='user', action='logout')
        logout_response = app.get(logout_url, status=302)
        final_response = helpers.webtest_maybe_follow(logout_response)
        return final_response