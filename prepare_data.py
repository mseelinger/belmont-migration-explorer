"""Build public aggregates from the private ncsbe_migration folder.
Run: python prepare_data.py /path/to/ncsbe_migration --out .
Raw records remain local; only explicitly selected aggregate fields are written.
"""
import argparse
import hashlib
import json
from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq

YEARS = list(range(2016, 2026))
FLOW_KEYS = ['origin_type','origin_state','origin_county','origin_name','origin_class','origin_confidence']

def age_band(values):
    age = pd.to_numeric(values, errors='coerce')
    return pd.cut(age.where(age.between(16, 110)), [15,24,34,44,54,64,110],
                  labels=['16–24','25–34','35–44','45–54','55–64','65+']).astype('string').fillna('Unknown / invalid')

def build(source, out):
    out.mkdir(parents=True, exist_ok=True)
    base = source/'outputs/GASTON_BELMONT'
    enriched = base/'map_outputs/enriched'
    people = pd.read_parquet(enriched/'belmont_migration_people_enriched_2016_2025.parquet')
    assert not people.duplicated(['ncid','cohort_year']).any()
    totals = people.groupby('cohort_year').size()
    validation = pd.read_csv(base/'validation/arrival_validation_by_year.csv')
    assert totals.equals(validation.set_index('year').total_arrivals.rename(None))
    coverage = pd.read_csv(enriched/'belmont_map_coverage_enriched.csv')
    flows = pd.read_csv(enriched/'map_ready/belmont_annual_flows_map_ready_2016_2025.csv')
    assert flows.groupby('cohort_year').movers.sum().equals(coverage.set_index('cohort_year').mapped_arrivals.rename('movers'))
    assert int(people.mapped_origin.sum()) == int(flows.movers.sum())
    flows.to_csv(out/'flows_enriched.csv', index=False)
    coverage.to_csv(out/'coverage_enriched.csv', index=False)
    validation.to_csv(out/'arrival_validation.csv', index=False)
    # Enrichment, registration timing, and age profiles include unmapped arrivals.
    dimensions = {'Origin classification':'origin_class', 'Origin resolution':'resolution_status',
                  'Registration timing':'registr_dt_timing', 'Prior NC snapshot':'prior_snapshot_class',
                  'Detailed evidence':'migration_detail', 'Age':'age_band'}
    people['age_band'] = age_band(people.age_at_end_snapshot)
    records=[]
    for label, field in dimensions.items():
        grouped=people.groupby(['cohort_year',field],dropna=False).size().reset_index(name='events')
        for y, category, n in grouped.itertuples(index=False,name=None):
            records.append(dict(year=y,population='Arrivals',dimension=label,category=str(category),events=n))
    snapshots={}
    cols=['ncid','county_desc','municipality_desc','status_cd','party_cd','age','precinct_desc','sex_code','race_code','snapshot_dt']
    for year in range(2016,2027):
        path=source/'snapshots'/f'snapshot_{year}0101.parquet'
        table=pq.read_table(path,columns=cols,filters=[('county_desc','=','GASTON'),('municipality_desc','=','BELMONT')]).to_pandas()
        assert table.snapshot_dt.eq(pd.Timestamp(year=year,month=1,day=1)).all()
        table=table[table.status_cd.ne('R')].copy()
        assert table.ncid.notna().all() and not table.ncid.duplicated().any()
        snapshots[year]=table.set_index('ncid')
    annual=[]; destinations=[]; cohort_sets={}
    profile_dims={'Party':'party_cd','Precinct':'precinct_desc','Sex code':'sex_code','Race code':'race_code'}
    for year in YEARS:
        start, end=snapshots[year], snapshots[year+1]
        a=set(end.index)-set(start.index); d=set(start.index)-set(end.index)
        assert a == set(people.loc[people.cohort_year.eq(year),'ncid']), f'Arrival set differs: {year}'
        cohort_sets[year]=a
        annual.append(dict(year=year,start_voters=len(start),arrivals=len(a),departures=len(d),retained=len(set(start.index)&set(end.index)),end_voters=len(end)))
        for population, frame in [('Arrivals',end.loc[sorted(a)]),('Departures',start.loc[sorted(d)]),('Ending electorate',end)]:
            frame=frame.copy(); frame['age_band']=age_band(frame.age)
            dims=dict(profile_dims)
            if population!='Arrivals': dims['Age']='age_band'
            for label,field in dims.items():
                for category,n in frame[field].fillna('Unknown').value_counts().items():
                    records.append(dict(year=year,population=population,dimension=label,category=str(category),events=int(n)))
        # Departures' destination evidence is the ending NC registration, not a confirmed move.
        last=pq.read_table(source/'snapshots'/f'snapshot_{year+1}0101.parquet',columns=['ncid','status_cd','county_desc','municipality_desc'],filters=[('ncid','in',sorted(d))]).to_pandas()
        for ncid in d:
            rows=last[last.ncid.eq(ncid)]
            current=rows[rows.status_cd.ne('R')]
            if len(current)==1:
                row=current.iloc[0]
                category=f"{row.county_desc} / {row.municipality_desc if pd.notna(row.municipality_desc) and row.municipality_desc else 'No municipality'}"
                evidence='Current NC registration elsewhere'
            elif len(current)>1:
                category='Multiple current NC records'; evidence='Unresolved'
            elif len(rows):
                category='Removed record only'; evidence='No current NC registration'
            else:
                category='Absent from NC snapshot'; evidence='No current NC registration'
            destinations.append(dict(year=year,destination=category,evidence=evidence,events=1))
    pd.DataFrame(annual).to_csv(out/'annual_summary.csv',index=False)
    pd.DataFrame(records).to_csv(out/'profiles.csv',index=False)
    pd.DataFrame(destinations).groupby(['year','destination','evidence'],as_index=False).events.sum().to_csv(out/'departure_destinations.csv',index=False)
    survival=[]
    for cohort, ids in cohort_sets.items():
        continuous=set(ids)
        for sy in range(cohort+1,2027):
            present=ids&set(snapshots[sy].index)
            continuous &= set(snapshots[sy].index)
            survival.append(dict(cohort_year=cohort,snapshot_year=sy,years_since_arrival=sy-cohort-1,cohort_size=len(ids),present=len(present),continuously_present=len(continuous)))
    pd.DataFrame(survival).to_csv(out/'cohort_retention.csv',index=False)
    # Latest uninterrupted observed registration spell partitions the 2026 electorate.
    spells={i:'Before 2016' for i in snapshots[2016].index}
    for y,ids in cohort_sets.items():
        for i in ids: spells[i]=str(y)
    composition=pd.Series([spells[i] for i in snapshots[2026].index]).value_counts().rename_axis('arrival_cohort').reset_index(name='voters')
    composition.to_csv(out/'current_composition.csv',index=False)
    ranges=[]
    for lo in YEARS:
        for hi in range(lo,2026):
            subset=people[people.cohort_year.between(lo,hi)]
            ranges.append(dict(start_year=lo,end_year=hi,arrival_events=len(subset),unique_arrivals=subset.ncid.nunique()))
    pd.DataFrame(ranges).to_csv(out/'arrival_ranges.csv',index=False)
    inventory=[]
    for path in sorted(source.rglob('*')):
        if not path.is_file(): continue
        relative=path.relative_to(source).as_posix()
        if not (relative.startswith('outputs/') or relative.startswith('snapshots/')): continue
        sha=hashlib.sha256()
        with path.open('rb') as file:
            for chunk in iter(lambda:file.read(8*1024*1024), b''): sha.update(chunk)
        role='Intermediate cache / audit evidence'
        if relative.startswith('snapshots/'): role='Annual stocks, arrivals, departures, profiles and retention'
        elif 'map_ready/' in relative: role='Geographic coordinates and enriched flow totals'
        elif 'enriched/belmont_' in relative: role='Final enriched classifications and coverage'
        elif 'validation/' in relative: role='Arrival reconciliation and prior snapshot evidence'
        elif relative.endswith('cohort_summary.csv'): role='Superseded summary; 2016 baseline mismatch'
        inventory.append(dict(file=relative,bytes=path.stat().st_size,sha256=sha.hexdigest(),role=role))
    pd.DataFrame(inventory).to_csv(out/'source_inventory.csv',index=False)
    metadata={'source_folder':'ncsbe_migration','snapshot_dates':[f'{y}-01-01' for y in range(2016,2027)],
              'geography':'county_desc = GASTON and municipality_desc = BELMONT', 'status_rule':'status_cd != R',
              'source_files':len(inventory),'arrival_events':len(people),'unique_arrivals':people.ncid.nunique(),
              'mapped_arrivals':int(flows.movers.sum()),'original_mapped_arrivals':int(pd.read_csv(base/'map_outputs/belmont_annual_flows_2016_2025.csv').movers.sum()),
              'quality_notes':['cohort_summary.csv reports 8,634 arrivals in 2016 (the ending stock). Snapshot sets and validation exports agree on 1,740 arrivals; the stale summary is not used.',
              'Ages outside 16–110 are reported as Unknown / invalid.', 'County/state centroid coordinates represent aggregate origin evidence, not individual addresses.']}
    (out/'data_metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(pd.DataFrame(annual).to_string(index=False))
    print(json.dumps(metadata,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('source',type=Path); parser.add_argument('--out',type=Path,default=Path('.'))
    args=parser.parse_args(); build(args.source,args.out)
