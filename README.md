# Belmont Migration Explorer

Tar Heel Tally’s Streamlit explorer of Belmont’s registered electorate, comparing January 1 snapshots from 2016 through 2026.

Live app: https://belmont-migration-explorer.streamlit.app/

## What is included

- Annual arrivals, departures, net registration change, electorate stocks and turnover rates.
- Enriched origin evidence, coverage, origin rankings and filtered CSV downloads.
- Combined-period migration map and animated annual maps, with stronger lines scaled by the square root of arrival counts and zero-count dots hidden.
- Arrival, departure and ending-electorate profiles by party, age, precinct, sex and race codes; additional arrival classification and registration-timing breakdowns.
- Ending-snapshot registration evidence for departures.
- Arrival cohort retention, distinguishing endpoint presence from continuous observed presence.
- January 1, 2026 electorate composition by latest observed arrival spell.
- Full source inventory, SHA-256 checksums and reconciliation notes.

All 75 files in the supplied `ncsbe_migration` source were retrieved: 11 annual snapshots and 64 output files. Final enriched tables provide origin evidence; older versions and restart caches support provenance and are not added together as extra voters.

The public app loads only aggregate CSVs. No individual voter identifiers, addresses, names or voter histories are published.

## Run and test

```bash
pip install -r requirements.txt
streamlit run app.py
```

For tests and private data preparation:

```bash
pip install -r requirements-dev.txt
pytest -q
python prepare_data.py /path/to/ncsbe_migration --out .
```

Keep the input folder outside the public repository. The source layout must contain `snapshots/snapshot_YYYY0101.parquet` and `outputs/GASTON_BELMONT/`, including the enriched map exports. `prepare_data.py` verifies exact agreement of annual arrival identifier sets with the enriched person export before writing public aggregates. It filters Parquet columns and rows so statewide records do not become app inputs.

Streamlit Community Cloud uses `app.py` at the repository root. Root CSV files are supported; a `data/` directory is also supported when all aggregate inputs are placed there.

## Definitions

Population: `county_desc = GASTON`, `municipality_desc = BELMONT`, and `status_cd != R`. This includes non-removed statuses, including inactive registrations. A Belmont mailing city does not define inclusion.

Arrivals and departures are NC identifier set differences between consecutive January 1 Belmont snapshots. Starting voters minus departures equals retained voters; retained plus arrivals equals ending voters. Counts describe registration membership changes and are not population migration estimates. Repeat arrivals are events; unique arrivals are calculated separately for each selected year range.

The full period contains 14,499 arrival events among 14,330 distinct people, 9,153 departure events and a net increase of 5,346 registrations. The electorate rises from 7,711 to 13,057. Enriched origins cover 10,293 events (71.0%), compared with 9,998 in the original export.

Observed prior registrations, historical NC registration/voting clues and inferred birthplace state proxies remain separate. None proves the immediately previous residence. Maps use supplied county/state centroids, not residential coordinates. Departure locations are current NC registration evidence from the ending snapshot; absent and removed-only records are not assumed interstate moves.

Arrival profile fields use the ending snapshot, departure profiles use the starting snapshot. Invalid ages outside 16–110 remain visible in an unknown group. Ending-electorate stocks are viewed one snapshot at a time. Party/demographic codes are reported as supplied, with no political conclusions inferred.

Cohort endpoint presence can rise after re-entry; continuous observed presence can only decline. Annual snapshots cannot detect between-snapshot changes. The 2026 composition assigns each current voter to their latest observed registration spell, or Before 2016 if no subsequent re-entry is observed.

## Data quality

`cohort_summary.csv` reports 8,634 arrivals for 2016, which is the ending electorate stock. It is superseded: snapshot identifier sets, validation exports and the enriched person export agree on 1,740 arrivals. The app uses the reconciled count. Original aggregate files remain available for comparison but are not the primary source for current charts.

The source inventory records filenames, sizes, hashes and roles. Files were obtained and aggregate tables generated October 3, 2026. Stored snapshot dates match January 1 filenames. The original raw extraction pipeline is not included in the Drive folder.
