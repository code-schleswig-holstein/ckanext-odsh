import logging
import traceback
import ast

log = logging.getLogger(__name__)


def odsh_openness_score_dataset_html(dataset):
    score = 0
    #dataset = json.loads(dataset)
    for resource in dataset.get('resources'):
        r_qa = resource.get('qa')
        if r_qa:
            try:
                qa = ast.literal_eval()
                resource_score = qa.get('openness_score')
                if resource_score > score:
                    score = resource_score
            except AttributeError, e:
                log.error('Error while calculating openness score %s: %s\nException: %s',
                    e.__class__.__name__,  unicode(e), traceback.format_exc())
    return score
