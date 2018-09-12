import json
import pyjq as pyjq

# Save all mappings from Statistikamt Nord numbers to MDR authority codes, which will be used to determine the CKAN-groups
with open('/usr/lib/ckan/default/src/ckanext-odsh/ckanext/odsh/harvesters/number_dcat_de.json') as f:
    numbers = json.load(f)

# Filter string needed by the pyjq-mapper, which is configured for the value we retrieve from Statistikamt Nord
config_filter = '{"author" : .VeroeffentlichendeStelle.Name,' \
                '"url" : .WeitereInformationen.URL,' \
                '"notes" : .Beschreibung,' \
                '"title" : .Titel,' \
                '"author_email": .VeroeffentlichendeStelle.EMailAdresse,' \
                '"extra": [' \
                '   {"key": "identifier", "value": (.Quelle + ":" +.DokumentID)},' \
                '   {"key": "issued", "value": .Veroeffentlichungsdatum?},' \
                '   {"key": "modified", "value": .Aenderungsdatum?},' \
                '   {"key": "temporal_start", "value": .ZeitraumVon?},' \
                '   {"key": "temporal_end", "value": .ZeitraumBis?}],' \
                '"resources" : [.Ressourcen.Ressource[] | {' \
                '   "url":.URLZumDownload,' \
                '   "size" : 50,' \
                '   "name" : .Ressourcenname,' \
                '   "format": .Format.FormatTyp }],' \
                '"license_id" : .Nutzungsbestimmungen.ID_derLizenz,' \
                '"type" : "dataset",' \
                '"tags" : [.Schlagwoerter |.Schlagwort[] | gsub(", "; ",") | select(length > 0) |' \
                '   split(",") |.[] |.+ "" | if (. | length) <= 100 then {"name" : .} else empty end],' \
                '"groups" : [$numbers[.StANKategorie][]? | {"name" : .}]}'

#"file_size" : (.Dateigroesse | tonumber | . * 1000),' \

def pyjq_mapper(value):
    print "value: " + str(value)

    tmp = pyjq.all(config_filter, value, vars={"numbers": numbers})

    print "tmp: " + str(tmp)
    return tmp[0]

# for testing reasons only
with open('/usr/lib/ckan/default/src/ckanext-odsh/ckanext/odsh/harvesters/statistik-nord-example_2.json') as f:
    input = json.load(f)
    print input
    result = dict(pyjq_mapper(input))
print result

