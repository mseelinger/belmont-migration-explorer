from pathlib import Path
import pandas as pd
import pytest
from model import load_arrivals, load_summary, load_flows, validate_flow_totals

DATA = Path(__file__).parent 

def test_recovered_totals():
    df = load_arrivals(DATA)
    assert df.arrivals.sum() == 14499
    assert df.year.tolist() == list(range(2016, 2026))

def test_summary_reconciliation_and_denominators(tmp_path):
    path = tmp_path / "summary.csv"
    pd.DataFrame([dict(year=2020,start_voters=9309,arrivals=2285,departures=949,retained=8360,end_voters=10645)]).to_csv(path,index=False)
    df = load_summary(path)
    assert df.iloc[0].arrival_rate_pct == pytest.approx(2285/10645*100)
    assert df.iloc[0].departure_rate_pct == pytest.approx(949/9309*100)
    df.loc[0,"end_voters"] = 1
    df.to_csv(path,index=False)
    with pytest.raises(ValueError):
        load_summary(path)

def test_invalid_counts_and_duplicates(tmp_path):
    for values in [[-1],[0.5],[None],[1,2]]:
        pd.DataFrame({"year":[2016]*len(values),"arrivals":values}).to_csv(tmp_path/"arrivals_recovered.csv",index=False)
        with pytest.raises(ValueError):
            load_arrivals(tmp_path)

def test_flow_coverage_and_private_columns(tmp_path):
    path = tmp_path / "flows.csv"
    pd.DataFrame([dict(cohort_year=2016, origin_type="NC_COUNTY",origin_state="NC",origin_county="GASTON",origin_name="Gaston County",origin_class="INTRASTATE",origin_confidence="OBSERVED",movers=1741,ncid="private")]).to_csv(path,index=False)
    df=load_flows(path)
    assert "ncid" not in df
    with pytest.raises(ValueError):
        validate_flow_totals(df,load_arrivals(DATA))
