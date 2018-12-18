import paste.fixture
import pylons.test
import ckan.plugins
import ckan.model as model
import ckan.tests.factories as factories
import ckan.tests.legacy as tests
from ckan.common import config


# class TestOdshPlugin(object):

#     @classmethod
#     def setup_class(cls):
#         cls.app = paste.fixture.TestApp(pylons.test.pylonsapp)
#         ckan.plugins.load('odsh')

#     def teardown(self):
#         model.repo.rebuild_db()

#     @classmethod
#     def teardown_class(cls):
#         ckan.plugins.unload('odsh')

#     def test_plugin(self):
#         pass

#     def test_user_cannot_access_dashboard(self):
#         user = factories.User()
#         tests.call_action_api(self.app, 'group_create', name='test-group',
#                               apikey=user['apikey'])
