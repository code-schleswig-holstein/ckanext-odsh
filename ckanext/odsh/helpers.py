import logging
import traceback
import ast
import ckan.plugins.toolkit as toolkit

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
    
