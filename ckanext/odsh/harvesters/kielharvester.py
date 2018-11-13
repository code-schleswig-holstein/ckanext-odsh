from ckan import model
from ckan.logic import get_action
from ckan.plugins import toolkit
from ckanext.harvest.model import HarvestObject
from ckanext.odsh.harvesters.base import ODSHBaseHarvester

import requests
import uuid
import traceback
import json
import logging
import datetime

log = logging.getLogger(__name__)

GROUP_MAPPING = {'kultur_freizeit_sport_tourismus': 'educ', 'gesundheit': 'heal', 'politik_wahlen': 'gove',
                 'verwaltung': 'gove', 'infrastruktur_bauen_wohnen': 'regi', 'wirtschaft_arbeit': 'econ',
                 'transport_verkehr': 'tran', 'bildung_wissenschaft': 'educ', 'bevoelkerung': 'soci',
                 'gesetze_justiz': 'just', 'geo': 'regi', 'soziales': 'soci', 'umwelt_klima': 'envi'}


class KielHarvester(ODSHBaseHarvester):
    '''
    A Harvester for Kiel Open Data
    '''

    @staticmethod
    def info():
        return {
            'name': 'kiel',
            'title': 'Kiel Open Data',
            'description': 'Harvests Kiel Open Data',
            'form_config_interface': 'Text'
        }

    def gather_stage(self, harvest_job):
        url = harvest_job.source.url
        datasets = requests.get(url=url).json()

        try:
            used_identifiers = []
            ids = []
            for dataset in datasets:
                guid = str(uuid.uuid3(uuid.NAMESPACE_URL, dataset.get("url").encode('ascii', 'ignore')))
                obj = HarvestObject(job=harvest_job, guid=guid)
                obj.content = json.dumps(dataset)
                obj.save()
                log.info("harvest_object_id: %s, GUID: %s successfully gathered " % (str(obj.id), str(obj.guid)))
                used_identifiers.append(guid)
                ids.append(obj.id)

        except Exception as e:
            self._save_gather_error(
                'Statistik-Nord-Harvester: Error gathering the identifiers from the source server [%s]' % str(e),
                harvest_job)
            log.error(e)
            return None

        if len(ids) > 0:
            log.info(
                "finished %s IDs of %s IDs successfully gathered" % (len(used_identifiers), len(datasets)))
            log.debug("List of gathered IDs: %s" % ids)
            log.debug("gather_stage() finished: %s IDs gathered" % len(ids))
            return ids
        else:
            log.error("No records received")
            self._save_gather_error("Couldn't find any metadata files", harvest_job)
            return None

    @staticmethod
    def fetch_stage(harvest_object):
        if harvest_object:
            return True
        else:
            return False

    def import_stage(self, harvest_object):
        context = {
            'model': model,
            'session': model.Session,
            'user': self._get_user_name(),
        }
        if not harvest_object:
            log.error('Kiel-Harvester: No harvest object received')
            return False

        if harvest_object.content is None:
            self._save_object_error('Empty content for object %s' % harvest_object.id, harvest_object, u'Import')
            return False
        else:
            package_dict = json.loads(harvest_object.content)
            published = str()
            for date in package_dict['extras']['dates']:
                if date['role'] == 'veroeffentlicht':
                    published = date['date']
            package_dict['metadata_modified'] = datetime.datetime.strptime(published, "%d.%m.%Y").isoformat()
            source_dataset = get_action('package_show')(context.copy(), {'id': harvest_object.source.id})
            package_dict['owner_org'] = source_dataset.get('owner_org')

            if package_dict['type'] == 'datensatz':
                package_dict['type'] = 'dataset'
            package_dict['id'] = harvest_object.guid

            mapped_groups = list()
            for group in package_dict['groups']:
                if GROUP_MAPPING[group]:
                    mapped_groups.append({'name': GROUP_MAPPING[group]})
            package_dict['groups'] = mapped_groups

            package_dict['extras'] = list()
            package_dict['extras'].append({'key': 'spatial', 'value': '{"type":"Polygon","coordinates":[[[10.174111899524393,54.345769038281475],[10.180109128884586,54.34735526991759],[10.18541437024168,54.34167127322151],[10.204790034328457,54.34101034337313],[10.20179141964836,54.32448709716357],[10.215400517042644,54.330171093859654],[10.21862979439044,54.32448709716357],[10.213324553033345,54.31774561271007],[10.21009527568555,54.31959621628554],[10.189796960927975,54.314573149437834],[10.189796960927975,54.2979177172586],[10.205712684999256,54.289722187138665],[10.204098046325356,54.28469912029096],[10.208941962347051,54.2844347483516],[10.207557986340852,54.2771645200194],[10.205020696996156,54.27557828838328],[10.20156075698066,54.27927949553422],[10.199254130303663,54.27795763583746],[10.201099431645261,54.26645745647561],[10.186798346247878,54.25958378605243],[10.183799731567781,54.25323885950796],[10.174342562192093,54.252710115629256],[10.170651959508897,54.25654350874987],[10.158888163456211,54.25905504217373],[10.154044247434516,54.258261926355665],[10.15219894609292,54.250859512053786],[10.13466858334774,54.25773318247696],[10.123366112630453,54.255486020992464],[10.123135449962755,54.258261926355665],[10.113678280587065,54.2609056457492],[10.094533279167988,54.263152807233695],[10.083692133786101,54.26844024602075],[10.091534664487892,54.274785172565224],[10.094994604503388,54.28707846774513],[10.0846147844569,54.289722187138665],[10.066853759044022,54.28496349223031],[10.057627252336033,54.2884003274419],[10.05947255367763,54.29699241547087],[10.047939420292645,54.298578647106986],[10.045863456283346,54.30822822289336],[10.05186068564354,54.31126850019592],[10.042172853600151,54.312061616013985],[10.04286484160325,54.3226364935881],[10.053244661649739,54.33426885891963],[10.06916038572102,54.32567677089066],[10.09291864049409,54.32845267625386],[10.105374424549876,54.3366482063738],[10.097301231180385,54.35052773318983],[10.09245731515869,54.345769038281475],[10.070544361727217,54.34378624873633],[10.06846839771792,54.34841275767501],[10.050246046969642,54.3456368523118],[10.032715684224463,54.34933805946274],[10.035714298904558,54.360045123006536],[10.061548517686928,54.360045123006536],[10.06916038572102,54.36387851612715],[10.072850988404214,54.37194186027742],[10.081846832444503,54.36943032685356],[10.103067797872878,54.37220623221677],[10.118983521944159,54.36956251282324],[10.139743162037135,54.38806854857794],[10.13351527000924,54.393355987365],[10.13443792068004,54.41344825475582],[10.146432379400427,54.41080453536229],[10.157273524782314,54.42917838514732],[10.1692679835027,54.431425546631814],[10.188874310257175,54.41106890730165],[10.19279557560807,54.39031571006244],[10.176187863533691,54.389786966183735],[10.161194790133209,54.38516045724506],[10.166730694158002,54.377890228912854],[10.154044247434516,54.36890158297486],[10.139512499369435,54.36850502506583],[10.148508343409723,54.366390049551],[10.139051174034035,54.36572911970262],[10.15196828342522,54.36334977224845],[10.147124367403526,54.363481958218124],[10.149892319415923,54.35925200718847],[10.145509728729628,54.36110261076394],[10.141357800711033,54.353964568401416],[10.155197560773015,54.34497592246342],[10.157734850117713,54.338366623979596],[10.136283222021639,54.31748124077072],[10.132592619338443,54.31126850019592],[10.148739006077424,54.32184337777004],[10.15219894609292,54.319728402255215],[10.15058430741902,54.323958353284866],[10.16073346479781,54.3226364935881],[10.170421296841198,54.32898142013257],[10.166961356825702,54.33559071861639],[10.170651959508897,54.33757350816154],[10.17711051420449,54.33453323085898],[10.172958586185894,54.33757350816154],[10.174111899524393,54.345769038281475]]]}'})

            for resource in package_dict['resources']:
                resource['name'] = package_dict['title']
                resource['description'] = package_dict['notes']

            tags = package_dict['tags']
            package_dict['tags'] = list()
            for tag in tags:
                seperated_tags = tag.split(',')
                for seperated_tag in seperated_tags:
                    if seperated_tag != '' and len(seperated_tag) < 100:
                        package_dict['tags'].append({'name': seperated_tag.strip()})

            license_id = self._get_license_id(package_dict['license_id'])
            if license_id:
                package_dict['license_id'] = license_id
            else:
                log.error('invalid license_id: %s' % package_dict['license_id'])
                self._save_object_error('Invalid license_id: %s' % package_dict['license_id'], harvest_object, 'Import')
                return False
            try:
                result = self._create_or_update_package(package_dict, harvest_object, package_dict_form='package_show')
                return result
            except toolkit.ValidationError as e:
                self._save_object_error('Validation Error: %s' % str(e.error_summary), harvest_object, 'Import')
                return False
