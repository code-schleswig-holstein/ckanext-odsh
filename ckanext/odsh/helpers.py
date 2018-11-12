import logging
import traceback
import ast
import ckan.plugins.toolkit as toolkit
import ckan.logic as logic
import ckan.model as model
from ckan.common import  c

get_action = logic.get_action
log = logging.getLogger(__name__)

def odsh_openness_score_dataset_html(dataset):
    score = 0
    #dataset = json.loads(dataset)
    resources = dataset.get('resources')
    if resources is None:
        return 0
    for resource in resources:
        r_qa = resource.get('qa')
        if r_qa:
            try:
                qa = None
                if isinstance(r_qa, basestring): # r_qa might be a string of a dictionary when 'dataset' is send from solr
                    qa = ast.literal_eval(r_qa)
                else:
                    qa = r_qa
                resource_score = qa.get('openness_score')
                if resource_score > score:
                    score = resource_score
            except AttributeError, e:
                log.error('Error while calculating openness score %s: %s\nException: %s',
                    e.__class__.__name__,  unicode(e), traceback.format_exc())
    return score

def odsh_get_resource_details(resource_id):
    resource_details = toolkit.get_action('resource_show')(
        data_dict={'id': resource_id})
    return resource_details
    

def odsh_get_resource_views(pkg_dict, resource):

        context = {'model': model, 'session': model.Session,
                   'user': c.user, 'for_view': True,
                   'auth_user_obj': c.userobj}
        return get_action('resource_view_list')(
            context, {'id': resource['id']})

