from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).parent

def test_loaded_app_and_year_scope():
    app=AppTest.from_file(str(ROOT/'app.py')).run(timeout=30)
    assert not app.exception
    assert app.metric[0].value=='14,499'
    assert app.metric[1].value=='9,153'
    assert app.metric[3].value=='14,330'
    app.select_slider[0].set_value((2020,2020)).run(timeout=30)
    assert not app.exception
    assert app.metric[0].value=='2,285'
    assert app.metric[1].value=='949'
    assert app.metric[2].value=='+1,336'

def test_evidence_profiles_and_retention_controls():
    app=AppTest.from_file(str(ROOT/'app.py')).run(timeout=30)
    assert not app.exception
    assert any(m.value=='10,293' for m in app.metric)
    app.multiselect[0].set_value([]).run(timeout=30)
    assert not app.exception
    assert any('No origins match' in i.value for i in app.info)
    app.multiselect[0].set_value(['HISTORICAL_OBSERVED']).run(timeout=30)
    assert not app.exception
    assert any('303 arrival events match' in i.value for i in app.caption)
    app.radio[0].set_value('Animate annual cohorts').run(timeout=30)
    assert not app.exception
    app.radio[2].set_value('Ending electorate').run(timeout=30)
    assert not app.exception
    app.radio[3].set_value('Continuously present').run(timeout=30)
    assert not app.exception
