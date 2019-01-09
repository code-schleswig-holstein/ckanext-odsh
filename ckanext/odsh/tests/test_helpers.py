import ckan.tests.helpers as helpers

def odsh_test(): return helpers.change_config('ckanext.odsh.spatial.mapping',
                                              'file:///usr/lib/ckan/default/src/ckanext-odsh/ckanext/odsh/tests/spatial_mapping.csv')