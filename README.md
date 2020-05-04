# ckanext-odsh
Diese CKAN-Extension enthält die wichtigsten Features und das Layout für das Tranzparenzportal Schleswig-Holstein.
Sie ist eine Weiterentwicklung der gleichnamigen Extension, die im Zuge der Entwicklung des Open Data Portals Schleswig-Holstein entwickelt wurde.

## Branches
### master
Dieser Branch enthält den aktuell auf den Stage- bzw. Prod-Servern laufenden Code.

### dev
Dieser Branch enthält den aktuellsten Stand mit allen fertig entwickelten Features.

### andere Branches
Für die Entwicklung neuer Features soll jeweils ein eigener Branch vom dev-Branch abgezweigt werden. Für den Branch soll ein sprechender Name gewählt werden.

## Deployment auf Produktivsystem
Das Deployment auf das Produktivsystem geschieht über Ansible. Die dafür benötigten Skripte befinden sich im Repository `tpsh_deploy`. 

## Manuelle Installation


## Konfiguration
Die Extension benötigt Konfigurationsparameter in der CKAN-Konfigurationsdatei (z.B. `production.ini`). Die korrekten Parameter für das Produktivsystem befinden sich im Repository `tpsh_deploy` unter `resources/production.ini`. Folgende Parameter sollten für Enwicklungssysteme geändert werden:

| Parameter                             | Erläuterung                                                   | Wert für Entwicklungssysteme              |
|---------------------------------------|---------------------------------------------------------------|-------------------------------------------|
| ckanext.odsh.use_matomo               | `true` schaltet das matomo-Tracking ein.                      | `false`                                   |
| ckanext.odsh.skip_icap_virus_check    | `false` schaltet den Virus-Check ein.                         | `true`                                    |
| ckanext.odsh.showtestbanner           | `true` schaltet das Banner "Testsystem" ein, Muss `false` für Production-Server sein. | -                 |