#!/usr/bin/env python
"""
Some Variables needed for configuration of the ckan_mapper function.
It supplys a filter string needed by the pyjq-mapper and a dicitonary containing the statistikamt nord
category numbers and the corresponding MDR data-theme authority codes.

The config_filter string is build up like a json string.
To generate this string, visit https://stedolan.github.io/jq/manual/.
The keys are valid CKAN-Fields, and the values are the paths to
the corresponding values within the Statistikamt Nord datasets.
"""

config_filter = '{"author" : .VeroeffentlichendeStelle.Name,' \
                '"url" : .WeitereInformationen.URL,' \
                '"notes" : .Beschreibung,' \
                '"title" : .Titel,' \
                '"author_email": .VeroeffentlichendeStelle.EMailAdresse,' \
                '"extras": [' \
                '   {"key": "identifier", "value": (.Quelle + ":" +.DokumentID)},' \
                '   {"key": "issued", "value": .Veroeffentlichungsdatum?},' \
                '   {"key": "modified", "value": .Aenderungsdatum?},' \
                '   {"key": "temporal_start", "value": .ZeitraumVon?},' \
                '   {"key": "temporal_end", "value": .ZeitraumBis?},' \
                '   ([$numbers[.StANKategorie][]?] | {"key":"theme", "value": .})],' \
                '"resources" : [.Ressourcen.Ressource[] | {' \
                '   "url":.URLZumDownload,' \
                '   "size" : (.Dateigroesse | tonumber | . * 1000000 | floor),' \
                '   "name" : .Ressourcenname,' \
                '   "format": .Format.FormatTyp,' \
                '   "license": "dl-by-de/2.0"}],' \
                '"license_id" : "dl-by-de/2.0",' \
                '"type" : "dataset",' \
                '"tags" : [.Schlagwoerter |.Schlagwort[] | gsub(", "; ",") | select(length > 0) |' \
                '   split(",") |.[] |.+ "" | if (. | length) <= 100 then {"name" : .} else empty end],' \
                '"groups" : [$numbers[.StANKategorie][]? | {"name" : .}]}'

# This mapping should be exchanged by the official mapping list from statistikamt nord
numbers = {
"59" : ["econ", " agri"],
"56" : ["econ"],
"74" : ["econ"],
"48" : ["regi"],
"50" : ["regi"],
"68" : ["econ"],
"54" : ["econ"],
"116" : ["soci"],
"7" : ["soci"],
"9" : ["soci"],
"8" : ["soci"],
"93" : ["gove"],
"36" : ["educ"],
"75" : ["econ"],
"58" : ["tech"],
"90" : ["gove"],
"91" : ["gove"],
"73" : ["econ"],
"55" : ["econ"],
"31" : ["soci"],
"87" : ["ener", " envi"],
"60" : ["econ"],
"53" : ["econ"],
"52" : ["econ"],
"92" : ["gove"],
"10" : ["soci"],
"79" : ["gove", " econ"],
"72" : ["intr"],
"117" : ["regi"],
"49" : ["regi"],
"35" : ["regi"],
"43" : ["heal"],
"42" : ["heal", "soci"],
"64" : ["econ"],
"70" : ["intr"],
"69" : ["econ"],
"27" : ["soci"],
"28" : ["soci", "econ"],
"38" : ["educ"],
"108" : ["econ"],
"67" : ["econ"],
"66" : ["econ"],
"65" : ["econ"],
"46" : ["soci"],
"39" : ["intr"],
"57" : ["agri"],
"115" : ["agri"],
"80" : ["gove"],
"82" : ["gove"],
"47" : ["soci"],
"78" : ["soci"],
"40" : ["just"],
"85" : ["tran", "econ"],
"37" : ["educ"],
"45" : ["soci"],
"81" : ["gove"],
"84" : ["tran", "econ"],
"44" : ["heal"],
"71" : ["educ"],
"88" : ["envi"],
"86" : ["envi"],
"62" : ["econ"],
"63" : ["econ"],
"83" : ["tran", "envi", "ener"],
"77" : ["econ"],
"61" : ["econ"],
"98" : ["gove"],
"76" : ["econ"],
"89" : ["gove"],
"41" : ["educ"],
"51" : ["regi"],
"111" : ["soci", "regi"]
}
