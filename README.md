# Road per resident in US metro areas

Data and code behind the [maxmautner.com post *Too many roads*](https://maxmautner.com/2026/09/25/road-per-person.html), whose lead chart shows that Los Angeles has less public road per resident than any other US urbanized area over 1 million people.

![Meters of public road per resident, US urbanized areas over 1 million people, 2023](charts/road-per-resident.png)

## Source

Every number comes from one federal table:

[FHWA, *Highway Statistics 2023*, Table HM-71, "Urbanized Areas: Miles and Daily Vehicle-Miles Traveled" (January 7, 2025).](https://www.fhwa.dot.gov/policyinformation/statistics/2023/pdf/hm71.pdf)

For each Federal-Aid Urbanized Area, HM-71 reports the 2020 Census population, 2023 public road miles by functional class with a total, and 2023 daily vehicle-miles traveled (DVMT, in thousands) by functional class with a total.

## Method

1. Take every urbanized area with a 2020 population of at least 1,000,000, excluding Puerto Rico. That yields 41 areas.
2. From each, use three published figures: population, total road miles, and total daily vehicle-miles.
3. Compute:

| Metric | Formula |
|---|---|
| Meters of road per resident | total miles × 1,609.344 ÷ population |
| Residents per mile of road | population ÷ total miles |
| Daily vehicle-miles per road mile | DVMT × 1,000 ÷ total miles |
| Daily vehicle-miles per resident | DVMT × 1,000 ÷ population |

The regional aggregates (`data/regional-aggregates-2023.csv`) add up the separately reported urbanized areas that make up greater Southern California (11 areas) and the Bay Area (12 areas), because the Census splits outlying suburbs such as Santa Clarita and Concord from the core areas. The member lists are in `scripts/build_metrics.py`.

A hand check for any row: Atlanta has 4,515,419 residents and 25,388 miles of road. 25,388 × 1,609.344 ÷ 4,515,419 = 9.05 meters per resident.

## Reproduce

```
pip install -r requirements.txt
playwright install chromium     # only for the charts
make
```

or step by step:

```
python scripts/fetch_hm71.py        # download the PDF to data/raw/, print its SHA-256
python scripts/parse_hm71.py        # every row of the table -> data/hm71_2023_all_areas.csv
python scripts/build_metrics.py     # -> data/us-metro-road-per-resident-2023.csv, data/regional-aggregates-2023.csv
python scripts/render_charts.py     # -> charts/*.png
```

`parse_hm71.py` checks its own extraction two ways: each row's functional-class columns must sum to that row's published total, and the sum of all parsed rows must match the table's own TOTAL row (population exactly, other columns within accumulated rounding). If a row is dropped or split during PDF extraction, the second check fails.

`data/reference/hm71_2023_rows_used.txt` is the text of every HM-71 row this analysis uses, as extracted from the PDF. `python scripts/parse_hm71.py data/reference/hm71_2023_rows_used.txt` followed by `python scripts/build_metrics.py` reproduces the published CSVs without downloading anything.

## Caveats

- Miles are centerline miles. FHWA does not record road width, and it assumes two lanes for all local streets, so neither pavement area nor true lane-miles can be computed from this table.
- Population is the 2020 Census count as printed in HM-71; miles and travel are 2023.
- DVMT counts all travel on an area's roads, including through traffic, not only trips by residents.
- FHWA notes that urbanized areas or data "may be missing or unreported in some States." Local road mileage is the least carefully inventoried category, so middle-of-the-ranking differences of a few tenths of a meter are within the noise. The extremes are not.
- Census urbanized-area boundaries follow housing density, so the lowest-density exurbs of each metro fall outside them.

## Licenses

Code: MIT (see `LICENSE`).
FHWA data is a US government work in the public domain.
Fonts in `fonts/` (Crimson Pro, IBM Plex Sans) are under the SIL Open Font License; license texts are included.
