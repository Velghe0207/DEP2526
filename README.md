# DEP2 - 2025-2026 - groep12

Groepsleden: Emile Velghe, Korneel Grumieaux, Mikail In, Semih Malcikan en Yoran De Rop De Beukelaer

Dit project gaat over geanonimiseerde wifi data te scrapen van wifi routers en hiermee de totaal aanwezigheid en bezetting van een lokaal op een les per les basis te bepalen.

## Analysis

Hier zitten enkele bestanden die handig kunnen zijn bij het controleren van waarden.

- studentcountpersubgroep.ipynb: Telt het aantal studenten per subgroep

- userattandence.ipynb: Maakt een dataframe aan van de aanwezige studenten via de staging database.

## Data

Hier wordt alle data opgeslagen.

`archived`: Alle oude reservatie data wordt hierin bewaard

`classgroups`: Alle subgroepen opgehaald uit reservatie data via API van [dep2.simondg.com](dep2.simondg.com)

`cleaned`: Hier zit alle geformatte en opgeschonde data in

`incoming`: Nieuwe opgelaade reservatie data

`week1_4_wifi`: Wifidata van de eerste 4 weken gekregen van lectoren.

## Dwh

Hier in zitten alle scripts en bestanden om via .csv bestanden de datawarehouse en de database tabellen te creëren.

### Python:

- fill_dimroom.py: Verbindt met de database en vult tabel `dimRoom`
- fill_reservations.py: Verbindt met de database en vult tabel `FactSchedule`
- script_dimdate.py: Verbindt met de database en vult tabel `dimDate`
- script_dimsubgroep.py: Verbindt met de database en vult tabel `dimSubgroep`
- script_dimtime.py: Verbindt met de database en vult tabel `dimTime`
- script_staging_dimuser_bridgeusb.ipynb: Verbindt met de staging database en vult tabel `BridgeUserSubgroup`

### SQL:

- SQLCreateDimActivity.sql: Maakt tabel `dimActivity` aan en vult deze.
- SQLFillOccupancyRate.sql: Updates tabel 'FactSchedule' kolom OccupancyRate gebaseerd op lokaal capaciteit.
- SQLFillUserCountTotalStudents.sql: Vult tabel `FactSchedule` 'UserCount' en 'TotalStudents' via de staging database
- SQLStagingCreationQuery.sql: Maakt tabellen `dimUser`,`BridgeUserSubgroup` en `FactWifiConnection` aan in staging database.
- SteekProevenWeek10_11.sql: Script voor steekproeven van week 10 en 11 op te halen rechtstreeks uit database.

`lectures`: Alle scripts die te maken hebben met database tabel FactLecture.

- fillFactLectures.py: Verbindt met de database en vult tabel `FactSchedule`
- FormatLectures.py: Formateert lecture bestanden om deze te kunnen inlanden op de database.
- MergeLectures.py: Voegt alle lecture bestanden samen tot één bestand.

## Database

![DEP2 Database](dwh/sterschemaDEP2.png "DEP2 Database")

## Staging database

![DEP2 Staging database](dwh\sterschemaDEP2_staging.png "DEP2 Staging Database")

## Machine Learning

- ml.ipynb: Traint modellen op de data van `FactLecture` om het aantal aanwezige studenten te kunnen voorspellen.

## Power-bi

- PowerBI_reports.pbix: Power BI-dashboard bestand.

## Scraping

- class_processing.ipynb: Kuist en formateert gescrapte OLODS en vult database tabel `DimClass`.
- class_scraping.py: Scrapt alle OLODS van hogent.
- lokalen.ipynb: Kuist en formateert gekregen bestand van lokalen.
- reservations_clean_merge.ipynb:Kuist en formateert reservatie bestanden.
- students.ipynb: Haalt alle studenten op via API van [dep2.simondg.com](dep2.simondg.com) via gescrapte subgroepen in reservatie data.
- unique_classgroups_schedule.ipynb: Haalt alle unieke klasgroepen op uit reservatie data.
- week1_4_wifi.ipynb: Zet gekregen wifidata van de eerste 4 weken om tot bruikbare data.
- wifi_script.py: Scrapte wifi van de laaste 15 minutes via API van [dep2.simondg.com](dep2.simondg.com)
- wifi_script2_backup.py: Backup scraper van wifi data in geval van VM problemen.
