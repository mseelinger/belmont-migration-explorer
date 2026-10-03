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
