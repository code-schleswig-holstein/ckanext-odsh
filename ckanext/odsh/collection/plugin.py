
from ckan.lib.plugins import DefaultTranslation, DefaultDatasetForm
import ckan.plugins as plugins 
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

    
    # IRoutes    
    def before_map(self, map):

        map.connect(
            '/collection/{id}/aktuell',
            controller='ckanext.odsh.collection.controller:LatestDatasetController',
            action='latest_dataset'
        )

        map.connect(
            '/collection/{id}/aktuell.{type}',
            controller='ckanext.odsh.collection.controller:LatestRecourcesController',
            action='latest_resource'
        )

        with SubMapper(
            map, 
            controller='ckanext.odsh.collection.controller:LatestDatasetController', 
            path_prefix='/collection/'
        ) as m:
            m.connect('latest', '{id}/aktuell', action='latest')
            m.connect('latest_resource', '{id}/aktuell.{type}', action='latest_resource')  
        return map

    def after_map(self, map):
        return map

    
    # ITemplateHelpers
    def get_helpers(self):
        # Template helper function names should begin with the name of the
        # extension they belong to, to avoid clashing with functions from
        # other extensions.

        return {
            'collection_get_successor': collection_helpers.get_successor,
            'collection_get_predecessor': collection_helpers.get_predecessor,
            'collection_get_latest_member':collection_helpers.latest_collection_member_persistent_link,
            'collection_get_title': collection_helpers.get_collection_title_by_dataset,
        }
