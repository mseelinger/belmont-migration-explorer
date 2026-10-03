from pathlib import Path
from streamlit.testing.v1 import AppTest
import shutil
import pandas as pd

def test_app_and_year_filter():
    app = AppTest.from_file(str(Path(__file__).parent/"app.py")).run(timeout=30)
    assert not app.exception
    assert app.metric[0].value == "14,499"
    app.select_slider[0].set_value((2020,2020)).run()
    assert not app.exception
    assert app.metric[0].value == "2,285"

def test_full_exports_and_empty_origin_filter(tmp_path):
    root = Path(__file__).parent
    shutil.copy(root/"app.py", tmp_path/"app.py")
    shutil.copy(root/"model.py", tmp_path/"model.py")
    (tmp_path/"data").mkdir()
    pd.DataFrame([dict(year=2020,start_voters=9309,arrivals=2285,departures=949,retained=8360,end_voters=10645)]).to_csv(tmp_path/"data/annual_summary.csv", index=False)
    pd.DataFrame([dict(cohort_year=2020,origin_type="NC_COUNTY",origin_state="NC",origin_county="GASTON",origin_name="Gaston County",origin_class="INTRASTATE",origin_confidence="OBSERVED",movers=100)]).to_csv(tmp_path/"data/belmont_annual_flows_2016_2025.csv",index=False)
    app=AppTest.from_file(str(tmp_path/"app.py")).run(timeout=30)
    assert not app.exception
    assert any(m.value == "+1,336" for m in app.metric)
    app.multiselect[0].set_value([]).run()
    assert not app.exception
    assert any("No origins match" in item.value for item in app.info)
