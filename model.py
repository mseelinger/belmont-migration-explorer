"""Aggregate-only input contracts and calculations for the public explorer."""
from pathlib import Path
import pandas as pd


def counts(frame, columns):
    frame = frame.copy()
    for col in columns:
        values = pd.to_numeric(frame[col], errors="raise")
        if values.isna().any() or (values < 0).any() or (values % 1 != 0).any():
            raise ValueError(f"{col} must contain nonnegative whole numbers.")
        frame[col] = values.astype(int)
    return frame


def load_table(path, required, numeric, unique=None):
    frame = pd.read_csv(path)
    missing = set(required) - set(frame.columns)
    if missing:
        raise ValueError(f"{Path(path).name}: missing columns {', '.join(sorted(missing))}")
    # Allowlist prevents accidentally displaying identifiers or extra private columns.
    frame = counts(frame[list(required)], numeric)
    if unique and frame.duplicated(unique).any():
        raise ValueError(f"{Path(path).name}: duplicate rows for {unique}")
    return frame


def load_arrivals(directory):
    return load_table(directory / "arrivals_recovered.csv", ["year", "arrivals"],
                      ["year", "arrivals"], ["year"]).sort_values("year")


def load_summary(path):
    cols = ["year", "start_voters", "arrivals", "departures", "retained", "end_voters"]
    df = load_table(path, cols, cols, ["year"]).sort_values("year")
    if not (df.start_voters - df.departures == df.retained).all():
        raise ValueError("Starting voters minus departures must equal retained voters.")
    if not (df.retained + df.arrivals == df.end_voters).all():
        raise ValueError("Retained voters plus arrivals must equal ending voters.")
    previous = df.end_voters.shift()
    consecutive = df.year.diff().eq(1)
    if (consecutive & df.start_voters.ne(previous)).any():
        raise ValueError("Consecutive years must have matching end/start stocks.")
    df["net_change"] = df.arrivals - df.departures
    df["arrival_rate_pct"] = 100 * df.arrivals / df.end_voters.replace(0, float("nan"))
    df["departure_rate_pct"] = 100 * df.departures / df.start_voters.replace(0, float("nan"))
    df["retention_rate_pct"] = 100 * df.retained / df.start_voters.replace(0, float("nan"))
    return df


def load_flows(path):
    cols = ["cohort_year", "origin_type", "origin_state", "origin_county", "origin_name",
            "origin_class", "origin_confidence", "movers"]
    df = load_table(path, cols, ["cohort_year", "movers"], cols[:-1])
    for col in cols[1:-1]:
        df[col] = df[col].fillna("Unknown").astype(str)
    return df


def validate_flow_totals(flows, arrivals):
    totals = flows.groupby("cohort_year").movers.sum()
    lookup = arrivals.set_index("year").arrivals
    if not totals.index.isin(lookup.index).all():
        raise ValueError("Origin data contains years absent from the arrival totals.")
    if (totals > lookup.reindex(totals.index)).any():
        raise ValueError("Mapped origins exceed total arrivals for at least one year.")


def filter_years(frame, column, years):
    return frame[frame[column].between(*years)].copy()


def load_map_flows(path):
    df = load_flows(path)
    coordinates = pd.read_csv(path)[['origin_lat','origin_lon','dest_lat','dest_lon']].apply(pd.to_numeric,errors='raise')
    if coordinates.isna().any().any() or not coordinates[['origin_lat','dest_lat']].abs().le(90).all().all() or not coordinates[['origin_lon','dest_lon']].abs().le(180).all().all():
        raise ValueError('Invalid map coordinates.')
    return pd.concat([df,coordinates],axis=1)


def load_bundle(directory):
    import json
    annual=load_summary(directory/'annual_summary.csv')
    flows=load_map_flows(directory/'flows_enriched.csv')
    validate_flow_totals(flows,annual)
    coverage=load_table(directory/'coverage_enriched.csv',['cohort_year','total_arrivals','mapped_arrivals','mapped_share_pct'],['cohort_year','total_arrivals','mapped_arrivals'],['cohort_year'])
    if not coverage.set_index('cohort_year').total_arrivals.equals(annual.set_index('year').arrivals.rename('total_arrivals')):
        raise ValueError('Coverage arrival totals do not match annual stocks.')
    if not coverage.set_index('cohort_year').mapped_arrivals.equals(flows.groupby('cohort_year').movers.sum().rename('mapped_arrivals')):
        raise ValueError('Mapped coverage does not match origin totals.')
    profiles=load_table(directory/'profiles.csv',['year','population','dimension','category','events'],['year','events'],['year','population','dimension','category'])
    for (year,population,dimension), n in profiles.groupby(['year','population','dimension']).events.sum().items():
        column={'Arrivals':'arrivals','Departures':'departures','Ending electorate':'end_voters'}[population]
        if n != annual.set_index('year').loc[year,column]:
            raise ValueError(f'Profile does not reconcile: {year} {population} {dimension}')
    retention=load_table(directory/'cohort_retention.csv',['cohort_year','snapshot_year','years_since_arrival','cohort_size','present','continuously_present'],['cohort_year','snapshot_year','years_since_arrival','cohort_size','present','continuously_present'],['cohort_year','snapshot_year'])
    if (retention.continuously_present>retention.present).any() or (retention.present>retention.cohort_size).any():
        raise ValueError('Cohort retention exceeds its denominator.')
    destinations=load_table(directory/'departure_destinations.csv',['year','destination','evidence','events'],['year','events'],['year','destination','evidence'])
    if not destinations.groupby('year').events.sum().equals(annual.set_index('year').departures.rename('events')):
        raise ValueError('Departure evidence does not reconcile.')
    composition=load_table(directory/'current_composition.csv',['arrival_cohort','voters'],['voters'],['arrival_cohort'])
    if composition.voters.sum()!=annual.iloc[-1].end_voters:
        raise ValueError('Current electorate composition does not reconcile.')
    ranges=load_table(directory/'arrival_ranges.csv',['start_year','end_year','arrival_events','unique_arrivals'],['start_year','end_year','arrival_events','unique_arrivals'],['start_year','end_year'])
    metadata=json.loads((directory/'data_metadata.json').read_text())
    return annual,flows,coverage,profiles,retention,destinations,composition,ranges,metadata
