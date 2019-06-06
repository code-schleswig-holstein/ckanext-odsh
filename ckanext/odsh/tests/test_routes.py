from ckan.common import config
import ckan.model as model
import pdb
import json
import ckanext.odsh.profiles as profiles
import urllib2
import ckan.tests.helpers as helpers
from ckan.common import config
import ckan.config.middleware
from routes import url_for
webtest_submit = helpers.webtest_submit

# run with nosetests --ckan --nologcapture --with-pylons=<config to test> ckanext/odsh/tests/test_routes.py

def _get_test_app():
    app = ckan.config.middleware.make_app(config['global_conf'], **config)
    app = helpers.CKANTestApp(app)
    return app

class TestRoutes:

    def test_upload_empty_form_fails(self):
        # arrange
        self._login()
        form = self._get_package_new_form()

        # # act
        response = self._submit_form(form)

        # # assert
        # response.mustcontain('Title: Missing value')
        # response.mustcontain('Description: Missing value')
        # response.mustcontain('temporal_start: empty')


    def _get_package_new_form(self):
        # self.env = {'REMOTE_USER': 'ckanuser'}
        response = self.app.get(
            url=url_for(controller='package', action='new')
            # extra_environ=self.env,
        )
        return response.forms['dataset-edit']


    def _login(self):
        app = _get_test_app()
        response = app.get('/user/login')
        login_form = response.forms[0]
        login_form['login'] = 'ckanuser'
        login_form['password'] = 'pass'
        submit_response = login_form.submit('save')
        final_response = helpers.webtest_maybe_follow(submit_response)

        # the response is the user dashboard, right?
        # final_response.mustcontain('<a href="/dashboard">Dashboard</a>',
                                #    '<span class="username">sysadmin</span>')
        self.app = app

    def _submit_form(self, form):
        return webtest_submit(form, 'save', status=200)#, extra_environ=self.env)