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
    assert any('303 arrivals match' in i.value for i in app.caption)
    app.radio[0].set_value('Animate annual cohorts').run(timeout=30)
    assert not app.exception
    app.radio[2].set_value('Ending electorate').run(timeout=30)
    assert not app.exception
    app.radio[3].set_value('Continuously present').run(timeout=30)
    assert not app.exception


def test_profile_breakdown_survives_population_changes_and_age_order():
    app=AppTest.from_file(str(ROOT/'app.py')).run(timeout=30)
    app.selectbox(key='profile_breakdown').set_value('Age').run(timeout=30)
    app.radio[2].set_value('Departures').run(timeout=30)
    assert not app.exception
    assert app.selectbox(key='profile_breakdown').value=='Age'
    assert app.dataframe[0].value.category.tolist()==['16–24','25–34','35–44','45–54','55–64','65+','Unknown / invalid']
    app.radio[2].set_value('Ending electorate').run(timeout=30)
    assert app.selectbox(key='profile_breakdown').value=='Age'
    assert not app.exception
