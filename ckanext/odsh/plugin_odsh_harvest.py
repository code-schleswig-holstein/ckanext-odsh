import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.odsh.logic.action as action


class OdshHarvestPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IConfigurer)

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'harvest_templates')

    def before_map(self, map):
        DATASET_TYPE_NAME = 'harvest'
        controller = 'ckanext.odsh.controller:OdshHarvestController'
        
        map.connect('{0}_delete'.format(DATASET_TYPE_NAME), '/' +
                    DATASET_TYPE_NAME + '/delete/:id', controller=controller, action='delete')
        map.connect('{0}_refresh'.format(DATASET_TYPE_NAME), '/' + DATASET_TYPE_NAME + '/refresh/:id', controller=controller,
                    action='refresh')
        map.connect('{0}_admin'.format(DATASET_TYPE_NAME), '/' +
                    DATASET_TYPE_NAME + '/admin/:id', controller=controller, action='admin')
        map.connect('{0}_about'.format(DATASET_TYPE_NAME), '/' +
                    DATASET_TYPE_NAME + '/about/:id', controller=controller, action='about')
        map.connect('{0}_clear'.format(DATASET_TYPE_NAME), '/' +
                    DATASET_TYPE_NAME + '/clear/:id', controller=controller, action='clear')

        map.connect('harvest_job_list', '/' + DATASET_TYPE_NAME +
                    '/{source}/job', controller=controller, action='list_jobs')
        map.connect('harvest_job_show_last', '/' + DATASET_TYPE_NAME +
                    '/{source}/job/last', controller=controller, action='show_last_job')
        map.connect('harvest_job_show', '/' + DATASET_TYPE_NAME +
                    '/{source}/job/{id}', controller=controller, action='show_job')
        map.connect('harvest_job_abort', '/' + DATASET_TYPE_NAME +
                    '/{source}/job/{id}/abort', controller=controller, action='abort_job')

        map.connect('harvest_object_show', '/' + DATASET_TYPE_NAME +
                    '/object/:id', controller=controller, action='show_object')
        map.connect('harvest_object_for_dataset_show', '/dataset/harvest_object/:id',
                    controller=controller, action='show_object', ref_type='dataset')

        org_controller = 'ckanext.harvest.controllers.organization:OrganizationController'
        map.connect('{0}_org_list'.format(DATASET_TYPE_NAME), '/organization/' +
                    DATASET_TYPE_NAME + '/' + '{id}', controller=org_controller, action='source_list')
        return map

    def after_map(self, map):
        return map