
from ckan.lib.plugins import DefaultTranslation, DefaultDatasetForm
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import helpers as collection_helpers
from routes.mapper import SubMapper

class CollectionsPlugin(plugins.SingletonPlugin, DefaultDatasetForm):
    plugins.implements(plugins.IDatasetForm, inherit=True)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)


    # IDataSetForm
    def package_types(self):
        return ('collection', )
    
    def is_fallback(self):
        return False
    
    def read_template(self):
        return 'package/collection_read.html'

    
    # IRoutes    
    def before_map(self, map):

        map.connect(
            '/collection/{id}/aktuell',
            controller='ckanext.odsh.collection.controller:LatestDatasetController',
            action='latest_dataset'
        )

        map.connect(
            '/collection/{id}/aktuell.{resource_format}',
            controller='ckanext.odsh.collection.controller:LatestRecourcesController',
            action='latest_resource'
        )

        with SubMapper(
            map, 
            controller='ckanext.odsh.collection.controller:LatestDatasetController', 
            path_prefix='/collection/'
        ) as m:
            m.connect('latest', '{id}/aktuell', action='latest')
            m.connect('latest_resource', '{id}/aktuell.{resource_format}', action='latest_resource')  
        return map

    def after_map(self, map):
        return map

    
    # ITemplateHelpers
    def get_helpers(self):
        # Template helper function names should begin with the name of the
        # extension they belong to, to avoid clashing with functions from
        # other extensions.

        return {
            'get_collection': collection_helpers.get_collection,
            'get_collection_info': collection_helpers.get_collection_info,
            'url_from_id': collection_helpers.url_from_id,
        }
    