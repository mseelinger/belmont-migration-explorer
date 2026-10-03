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


def test_real_exports_reconcile():
    from model import load_bundle
    root=Path(__file__).parent
    annual,flows,coverage,profiles,retention,destinations,composition,ranges,meta=load_bundle(root)
    assert annual.arrivals.sum()==14499
    assert annual.departures.sum()==9153
    assert annual.iloc[-1].end_voters-annual.iloc[0].start_voters==5346
    assert flows.movers.sum()==10293
    assert composition.voters.sum()==13057
    assert meta['source_files']==75
    for cohort, group in retention.groupby('cohort_year'):
        assert group.sort_values('snapshot_year').continuously_present.diff().dropna().le(0).all()
        assert group.iloc[0].present==group.iloc[0].cohort_size
    assert ranges.unique_arrivals.le(ranges.arrival_events).all()


def test_map_animation_totals_and_widths():
    from maps import migration_map
    from model import load_map_flows
    flows=load_map_flows(Path(__file__).parent/'flows_enriched.csv')
    fig=migration_map(flows,animate=True,years=list(range(2016,2026)))
    assert len(fig.frames)==10
    for frame in fig.frames:
        lines=frame.data[:-2]
        assert sum(int(t.text[0].split('<br>')[1].split()[1].replace(',','')) for t in lines)==int(flows.loc[flows.cohort_year.eq(int(frame.name)),'movers'].sum())
        assert all(0<=t.line.width<=15 for t in lines)

        counts=[int(t.text[0].split('<br>')[1].split()[1].replace(',','')) for t in lines]
        assert all(size==0 for size,count in zip(frame.data[-2].marker.size,counts) if count==0)


def test_cumulative_composition_and_map_widths():
    from model import composition_shares
    from maps import line_width, route_points
    c=composition_shares(pd.read_csv(Path(__file__).parent/'current_composition.csv'))
    before2017=c[c['Arrived before'].eq('Before 2017')].iloc[0]
    assert before2017['Cumulative voters']==3042+717
    assert c.iloc[-1]['Cumulative voters']==13057
    assert c.iloc[-1]['Cumulative share (%)']==100
    assert c['Cumulative voters'].is_monotonic_increasing
    assert [line_width(n) for n in [0,1,11,51,201,1001]]==[0,1,2.5,5,9,15]
    lon,lat=route_points(40,-74,35.221172,-81.040091)
    assert len(lon)==240 and abs(lon[-1]+81.040091)<1e-8


def test_top_ten_map_route_highlights():
    from maps import migration_map, DARK_COLORS, LIGHT_COLORS
    from model import load_map_flows
    flows=load_map_flows(Path(__file__).parent/'flows_enriched.csv')
    fig=migration_map(flows,animate=True,years=[2016,2017])
    for traces in [fig.data]+[frame.data for frame in fig.frames]:
        for evidence,dark in DARK_COLORS.items():
            matching=[t for t in traces[:-2] if t.legendgroup==evidence and t.opacity>0]
            assert sum(t.line.color==dark for t in matching)==min(10,len(matching))
            counts=lambda t:int(t.text[0].split('<br>')[1].split()[1].replace(',',''))
            dark_counts=[counts(t) for t in matching if t.line.color==dark]
            light_counts=[counts(t) for t in matching if t.line.color==LIGHT_COLORS[evidence]]
            if light_counts: assert min(dark_counts)>=max(light_counts)
