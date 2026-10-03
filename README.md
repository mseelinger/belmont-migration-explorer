# Tar Heel Tally — Belmont Migration Explorer

Streamlit app for public exploration of changes in Belmont's registered electorate.
This version includes the original annual origin and coverage exports from the supplied Drive folder (modified August 29, 2026). It runs immediately with 2016–2025 arrival totals and origin exploration. It is a development starter, not a publication-ready
migration estimate. No synthetic origin, departure, or cohort values are included.

## Run locally

Use Python 3.11 or 3.12:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

On Windows, activate with `.venv\Scripts\activate`.

## GitHub and deployment

Create a repository named `belmont-migration-explorer` (or use an existing repository).
Upload this folder's contents so `app.py` and `requirements.txt` are at the repository root.
Alternatively initialize and push with Git:

```bash
git init -b main
git add .
git commit -m "Build Belmont migration explorer"
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

Then use Streamlit Community Cloud's Create app workflow, selecting the repository,
`main` branch and `app.py` entrypoint. Select the same Python version used locally.
GitHub stores the code; Streamlit runs the Python app. GitHub Pages cannot run this app.
Official guide: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy

## Load the original exports

The earlier analysis wrote files under:
`ncsbe_migration/outputs/GASTON_BELMONT/map_outputs/` in Google Drive.

1. Copy the latest aggregate `belmont_annual_flows_2016_2025.csv` into the repository root.
   Required columns: `cohort_year,origin_type,origin_state,origin_county,origin_name,origin_class,origin_confidence,movers`.
   One row per year/origin/evidence combination. Unmapped arrivals are not assumed to have a location.
2. Export the full annual stock/flow summary as `annual_summary.csv`.
   Required columns: `year,start_voters,arrivals,departures,retained,end_voters`.
   The app checks both stock identities and continuity between consecutive years.
3. Confirm snapshot dates, Belmont municipality field, inclusion of active/inactive
   statuses, and matching rules from the source pipeline. Document these before publication.
4. Reconcile recovered totals with the latest enriched outputs and archive the exact
   export date. The recovered annual arrival events total 14,499.

Origin totals must not exceed all arrivals. Extra columns are discarded by an allowlist.
The origin filters affect only the Origins tab; Overview continues to show all arrivals.
An inferred state is a proxy, not an observed previous state of residence.

Only reviewed aggregate exports belong in the public repository. Keep voter-level files,
names, addresses, NCIDs and source snapshots outside it; `private_data/` and Parquet
files are ignored, but this does not replace review of files before committing.

## Next data needed

- Departure destination aggregates, separating observed moves from removals/unresolved cases.
- Retention aggregates at cohort-year × observation-year grain, with cohort sizes and snapshot dates.
- Current electorate composition by first observed Belmont cohort (including baseline and reentries).
- Reviewed aggregate party/age/precinct dimensions and origin coordinates for maps.

These are intentionally unavailable until the underlying data supports them.

## Validation

```bash
pip install -r requirements-dev.txt
python -m pytest
```

## Included export validation
773 annual origin rows reconcile exactly to all 9,998 mapped arrival events in the coverage export; total arrivals are 14,499. The browser-upload layout keeps aggregate CSVs and test files at the repository root. The app also supports a data/ directory when used locally. Later enriched subfolder outputs have not yet been incorporated.
