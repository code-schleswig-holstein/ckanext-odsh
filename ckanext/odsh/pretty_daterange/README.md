# pretty_daterange package
Dieses Package erlaubt die "hübsche" Darstellung von Datumsbereichen. 

## Beispiel
```
from datetime import date
from pretty_daterange.date_range_formatter import DateRangeFormatter

drf = DateRangeFormatter(
    date_start = date(2019, 1, 1),
    date_end = date(2019, 3, 31)
)
print(drf.get_formatted_str())
```
prints
```
1. Quartal 2019
```

# Spezifikation
Viele Datumsangaben lassen sich eleganter als TT.MM.JJJJ-TT.MM.JJJJ darstellen. Bei der Anzeige auf der Suchergebnisseite und der Datensatzdetailsseite sollen Datumsangaben nach den folgenden Regeln umgeformt werden.

## Regel zum Kürzen von Datumsangaben
### Jahr ist gleich
Startdatum = a.b.n und Enddatum = a.b.n -> a.b.n

Starddatum = 01.01.n und Enddatum = 31.12.n -> n

Startdatum = 01.01.n und Enddatum = 31.01.n -> Januar n

Startdatum = 01.02.n und ( Enddatum = 28.02.n oder Enddatum = 28.02.n ) -> Februar n

Startdatum = 01.03.n und Enddatum = 31.03.n -> März n

[...]

Startdatum = 01.12.n und Enddatum = 31.12.n -> Dezember n

Startdatum = 01.01.n und Enddatum = 31.03.n -> 1. Quartal n

Startdatum = 01.04.n und Enddatum = 30.06.n -> 2. Quartal n

Startdatum = 01.07.n und Enddatum = 30.09.n -> 3. Quartal n

Startdatum = 01.10.n und Enddatum = 31.12.n -> 4. Quartal n

Startdatum = 01.01.n und Enddatum = 30.06.n -> 1. Halbjahr n

Startdatum = 01.07.n und Enddatum = 31.12.n -> 2. Halbjahr n

Startdatum = 01.01.n und ( Enddatum = 28.02.n oder Enddatum = 28.02.n ) -> Januar bis Februar n

Startdatum = 01.01.n und Enddatum = 31.03.n -> Januar bis März n

[...]

Startdatum = 01.01.n und Enddatum = 30.11.n -> Januar bis November n

### Jahr ist unterschiedlich
Startdatum = 01.01.n und Enddatum = 31.12.m -> n-m

Stardatum = 01.a.n und Enddatum ist letzer des Monats b im Jahr m -> [Text für a] n bis [Text für b] m
