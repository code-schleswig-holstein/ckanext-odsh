from ckanext.dcatde.profiles import DCATdeProfile, DCATDE, DCAT, VCARD, dcat_theme_prefix , DCATDE_1_0
from ckanext.dcat.utils import resource_uri
from ckanext.dcat.profiles import EuropeanDCATAPProfile, DCT, URIRefOrLiteral
from ckan.model.license import LicenseRegister
import rdflib
import ckanext.dcatde.dataset_utils as ds_utils
import logging
from ckan.plugins import toolkit
from ckan.common import config, json
from ckanext.dcat.interfaces import IDCATRDFHarvester

import sys
if sys.version_info[0] == 2:
    import urllib2
elif sys.version_info[0] == 3:  # >=Python3.1
    import urllib

log = logging.getLogger(__name__)
DCT = rdflib.namespace.Namespace("http://purl.org/dc/terms/")
DCAT = rdflib.namespace.Namespace("http://www.w3.org/ns/dcat#")

class ODSHEuropeanDCATAPProfile(EuropeanDCATAPProfile):

    def _license(self, dataset_ref):
        if self._licenceregister_cache is not None:
            license_uri2id, license_title2id = self._licenceregister_cache
        else:
            license_uri2id = {}
            license_title2id = {}
            for license_id, license in LicenseRegister().items():
                license_uri2id[license_id] = license_id 
                license_uri2id[license.url] = license_id
                license_title2id[license.title] = license_id
            self._licenceregister_cache = license_uri2id, license_title2id

        for distribution in self._distributions(dataset_ref):
            # If distribution has a license, attach it to the dataset
            license = self._object(distribution, DCT.license)
            if license:
                # Try to find a matching license comparing URIs, then titles
                license_id = license_uri2id.get(license.toPython())
                if not license_id:
                    license_id = license_title2id.get(
                        self._object_value(license, DCT.title))
                if license_id:
                    return license_id
        return ''

    def _distribution_format(self, distribution, normalize_ckan_format=True):
        imt, label = super(ODSHEuropeanDCATAPProfile,self)._distribution_format(distribution, normalize_ckan_format)            
        if label in resource_formats_import():
            label = resource_formats_import()[label]
        return imt, label
        
    def graph_from_dataset(self, dataset_dict, dataset_ref):
        super(ODSHEuropeanDCATAPProfile,self).graph_from_dataset(dataset_dict, dataset_ref)
        for s,p,o in self.g.triples((None, rdflib.RDF.type, DCAT.Distribution)):
            for s2, p2, o2 in self.g.triples((s, DCT['format'], None)):
                if o2.decode() in resource_formats_export():
                    self.g.set((s, DCT['format'], rdflib.URIRef(resource_formats_export()[o2.decode()])))
        for s,p,o in self.g.triples((None, DCT.language, None)):
            if o.decode() in get_language():
                 self.g.set((s, p, rdflib.URIRef(get_language()[o.decode()])))                 
            elif type(o) == rdflib.Literal and type(URIRefOrLiteral(o.decode())) == rdflib.URIRef:
                self.g.set((s, p, rdflib.URIRef(o.decode()) ))
        

class ODSHDCATdeProfile(DCATdeProfile):
    def parse_dataset(self, dataset_dict, dataset_ref):
        dataset_dict = super(ODSHDCATdeProfile,self).parse_dataset(dataset_dict, dataset_ref)
        # Enhance Distributions
        for distribution in self.g.objects(dataset_ref, DCAT.distribution):
            for resource_dict in dataset_dict.get('resources', []):
                # Match distribution in graph and distribution in ckan-dict
                if unicode(distribution) == resource_uri(resource_dict):
                    for namespace in [DCATDE, DCATDE_1_0]:
                        value = self._object_value(distribution, namespace.licenseAttributionByText)
                        if value:
                            ds_utils.insert_new_extras_field(dataset_dict, 'licenseAttributionByText', value)
                            return dataset_dict
        return dataset_dict

    def graph_from_dataset(self, dataset_dict, dataset_ref):
        super(ODSHDCATdeProfile,self).graph_from_dataset(dataset_dict, dataset_ref)
        # Enhance Distributions
        # <dcatde:contributorID rdf:resource="http://dcat-ap.de/def/contributors/schleswigHolstein"/>
        self.g.add((dataset_ref, DCATDE.contributorID, rdflib.URIRef("http://dcat-ap.de/def/contributors/schleswigHolstein")))

        
_RESOURCE_FORMATS_IMPORT = None
_RESOURCE_FORMATS_EXPORT = None

def resource_formats():
    global _RESOURCE_FORMATS_IMPORT
    global _RESOURCE_FORMATS_EXPORT
    _RESOURCE_FORMATS_IMPORT = {}
    _RESOURCE_FORMATS_EXPORT = {}
    g = rdflib.Graph()
    err_msg = ""
    # at first try to get the actual file list online:
    try:
        format_european_url = config.get('ckan.odsh.resource_formats_url')
        err_msg = "Could not get file formats from " + format_european_url
        if not format_european_url:
            log.warning("Could not find config setting: 'ckan.odsh.resource_formats_url', using fallback instead.")
            format_european_url = "http://publications.europa.eu/resource/authority/file-type"
        if sys.version_info[0] == 2:
            urlresponse = urllib2.urlopen(urllib2.Request(format_european_url))
        elif sys.version_info[0] == 3:  # >=Python3.1
            urlresponse = urllib.request.urlopen(urllib.request.Request(format_european_url))
        g.parse(urlresponse)
        # At the moment, there are 143 different file types listed, 
        # if less than 120 are found, something went wrong.
        assert len(set([s for s in g.subjects()])) > 120
        # Save the content as backup
        if sys.version_info[0] == 2:
            urlresponse = urllib2.urlopen(urllib2.Request(format_european_url))
        elif sys.version_info[0] == 3:  # >=Python3.1
            urlresponse = urllib.request.urlopen(urllib.request.Request(format_european_url))
        err_msg = "Could not write to /usr/lib/ckan/default/src/ckanext-odsh/ckanext/odsh/fileformats.rdf"
        f = open('/usr/lib/ckan/default/src/ckanext-odsh/ckanext/odsh/fileformats.rdf', 'w')
        f.write(urlresponse.read())
        f.close()
    except:
        # Something went wrong with trying to get the file formats online, try to use backup instead
        try:
            g.parse('/usr/lib/ckan/default/src/ckanext-odsh/ckanext/odsh/fileformats.rdf')
            assert len(set([s for s in g.subjects()])) > 120
            log.warning("Could not get file formats from " + format_european_url + ", using fallback instead.")
        except:
            raise Exception(err_msg)
    file_types = [subj.decode() for subj in g.subjects()]
    
    for elem in sorted(set(file_types)):
        if elem.split('/')[-1] != 'file-type':
            _RESOURCE_FORMATS_EXPORT[elem.split('/')[-1]] = elem
            _RESOURCE_FORMATS_IMPORT[elem] = elem.split('/')[-1]

def resource_formats_export():
    global _RESOURCE_FORMATS_EXPORT
    if not _RESOURCE_FORMATS_EXPORT:
        resource_formats()
    return _RESOURCE_FORMATS_EXPORT
    
def resource_formats_import():
    global _RESOURCE_FORMATS_IMPORT
    if not _RESOURCE_FORMATS_IMPORT:
        resource_formats()
    return _RESOURCE_FORMATS_IMPORT

    
_LANGUAGES = None

def get_language():
    ''' When datasets are exported in rdf-format, their language-tag 
    should be given as
    "<dct:language rdf:resource="http://publications.europa.eu/.../XXX"/>",
    where XXX represents the language conforming to iso-639-3 standard.
    However, some imported datasets represent their language as
    "<dct:language>de</dct:language>", which will be interpreted here as 
    iso-639-1 values. As we do not display the language setting in the 
    web frontend, this function only assures the correct export format,
    by using 'languages.json' as mapping table.
    '''
    global _LANGUAGES
    if not _LANGUAGES:
        _LANGUAGES = {}
        languages_file_path = config.get('ckanext.odsh.language.mapping')
        if not languages_file_path:
            log.warning("Could not find config setting: 'ckanext.odsh.language.mapping', using fallback instead.")
            languages_file_path = '/usr/lib/ckan/default/src/ckanext-odsh/languages.json'
        with open(languages_file_path) as languages_file:
            try:
                language_mapping_table = json.loads(languages_file.read())
            except ValueError, e:
                # includes simplejson.decoder.JSONDecodeError
                raise ValueError('Invalid JSON syntax in %s: %s' %
                                 (languages_file_path, e))

            for language_line in language_mapping_table:
                _LANGUAGES[language_line[0]] = language_line[1]

    return _LANGUAGES
