import nose.tools as nt
from mock import patch
from ckan.common import config

from ckanext.odsh.plugin import OdshPlugin
import ckanext.odsh.helpers_tpsh as helpers_tpsh
import ckanext.odsh.matomo as matomo

class Test_helper_odsh_use_matomo(object):
    def setUp(self):
        self.plugin = OdshPlugin()
    
    def test_use_matomo_returns_False_if_not_in_config(self):
        use_matomo = self.plugin.get_helpers()['odsh_use_matomo']()
        nt.assert_false(use_matomo)
    
    def test_use_matomo_returns_False_if_set_False_in_config(self):
        config.update({'ckanext.odsh.use_matomo': 'False'})
        use_matomo = self.plugin.get_helpers()['odsh_use_matomo']()
        nt.assert_false(use_matomo)
        config.clear()
    
    def test_use_matomo_returns_True_if_set_True_in_config(self):
        config.update({'ckanext.odsh.use_matomo': 'True'})
        use_matomo = self.plugin.get_helpers()['odsh_use_matomo']()
        nt.assert_true(use_matomo)
        config.clear()
    

class Test_decorator_do_if_use_matomo(object):
    def test_it_does_not_if_use_matomo_set_False_in_config(self):
        
        @matomo.do_if_use_matomo
        def set_to_true(_):
            return True
        
        config.update({'ckanext.odsh.use_matomo': 'False'})
        did_run = False
        did_run = set_to_true(did_run)
        nt.assert_false(did_run)
        config.clear()
    
    def test_it_does_if_use_matomo_set_True_in_config(self):
        
        @matomo.do_if_use_matomo
        def set_to_true(_):
            return True

        config.update({'ckanext.odsh.use_matomo': 'True'})
        did_run = False
        did_run = set_to_true(did_run)
        nt.assert_true(did_run)
        config.clear()
