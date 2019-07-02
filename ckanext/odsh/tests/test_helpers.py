import contextlib
import errno
import functools
from ckan.common import config
import ckan.config.middleware
import ckan.tests.helpers as helpers
import sys
import pdb


def odsh_test():
    return change_config()


def change_config():
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with changed_config():
                return func(*args, **kwargs)
        return wrapper
    return decorator


@contextlib.contextmanager
def changed_config():
    _original_config = config.copy()
    config['ckanext.odsh.spatial.mapping'] = 'file:///usr/lib/ckan/default/src/ckanext-odsh/ckanext/odsh/tests/spatial_mapping.csv'
    config['licenses_group_url'] = 'file:///usr/lib/ckan/default/src/ckanext-odsh/licenses.json'
    try:
        yield
    finally:
        config.clear()
        config.update(_original_config)


def _get_test_app():
    app = ckan.config.middleware.make_app(config['global_conf'], **config)
    app = helpers.CKANTestApp(app)
    return app


def getConfigPath():
    path = None
    for a in sys.argv:
        if a.startswith('--with-pylons'):
            path = a.split('=')[1]
            break
    assert path, 'could not find config parameter'
    return path

class AppProxy:
    def login(self):
        app = _get_test_app()
        response = app.get('/user/login')
        login_form = response.forms[0]

        user = config.get('ckanext.odsh.testuser', None)
        assert user 
        password = config.get('ckanext.odsh.testuserpass', None)
        assert password 
        login_form['login'] = user
        login_form['password'] = password
        submit_response = login_form.submit('save')
        final_response = helpers.webtest_maybe_follow(submit_response)
        self.app = app

    def get(self, path):
        return self.app.get(path)

    def submit_form(self, form):
        submit_response = form.submit('save')
        final_response = helpers.webtest_maybe_follow(submit_response)
        # let's go to the last redirect in the chain
        return final_response