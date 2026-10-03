from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from model import load_arrivals, load_summary, load_flows, validate_flow_totals, filter_years

st.set_page_config(page_title="Belmont Migration Explorer | Tar Heel Tally", page_icon="📊", layout="wide")
DATA = Path(__file__).parent / "data"
if not DATA.exists():
    DATA = Path(__file__).parent
BLUE, ORANGE = "#2878A5", "#E78A38"
st.caption("TAR HEEL TALLY")
st.title("Belmont Migration Explorer")
st.write("Explore changes in Belmont’s registered electorate and the evidence about where new registrations came from.")

summary_path = DATA / "annual_summary.csv"
try:
    annual = load_summary(summary_path) if summary_path.exists() else load_arrivals(DATA)
    flow_path = DATA / "belmont_annual_flows_2016_2025.csv"
    flows = load_flows(flow_path) if flow_path.exists() else None
    if flows is not None:
        validate_flow_totals(flows, annual)
except (ValueError, KeyError, OSError) as error:
    st.error(f"Unable to load the dataset: {error}")
    st.stop()

full = summary_path.exists()
if not full:
    st.info("Arrival and origin aggregates loaded from your Drive exports (modified August 29, 2026). Departures, electorate size and retention are not yet loaded; exact snapshot dates still need confirmation.")
years = sorted(annual.year.unique().tolist())
with st.sidebar:
    st.header("Explore the data")
    selected = st.select_slider("Years", options=years, value=(years[0], years[-1]))
    st.caption("Years identify snapshot-comparison cohorts; exact snapshot dates are awaiting the original exports.")
view = filter_years(annual, "year", selected)
overview, origins, methods = st.tabs(["Overview", "Origins", "Data & methods"])

def chart(fig):
    fig.update_layout(template="plotly_white", margin=dict(l=0, r=0, t=25, b=0),
                      legend_title_text="", font=dict(color="#203344"))
    fig.update_xaxes(dtick=1)
    st.plotly_chart(fig, use_container_width=True)

with overview:
    cols = st.columns(3)
    cols[0].metric("Arrival events", f"{view.arrivals.sum():,}")
    cols[1].metric("Years selected", str(len(view)))
    cols[2].metric("Annual average arrivals", f"{view.arrivals.mean():,.0f}")
    st.caption("An arrival is present in the ending Belmont snapshot and absent from the starting Belmont snapshot. Counts across years are events, not unique people or confirmed residential moves.")
    st.subheader("Arrivals over time" if not full else "Arrivals and departures over time")
    fig = go.Figure(go.Bar(x=view.year, y=view.arrivals, name="Arrivals", marker_color=BLUE))
    if full:
        fig.add_bar(x=view.year, y=view.departures, name="Departures", marker_color=ORANGE)
        fig.add_scatter(x=view.year, y=view.net_change, name="Net registration change", mode="lines+markers", line=dict(color="#203344"))
    fig.update_layout(barmode="group", yaxis_title="Registration events")
    chart(fig)
    if full:
        year = st.selectbox("Inspect a cohort year", view.year.tolist(), index=len(view)-1)
        row = view[view.year.eq(year)].iloc[0]
        cards = st.columns(4)
        for col, label, value in zip(cards, ["Starting electorate", "Ending electorate", "Net registration change", "One-period retention"],
                                      [f"{row.start_voters:,.0f}", f"{row.end_voters:,.0f}", f"{row.net_change:+,.0f}", f"{row.retention_rate_pct:.1f}%"]):
            col.metric(label, value)
        st.caption("One-period retention = retained ÷ starting voters. This is not a multi-year cohort survival curve.")
        rates = view.melt(id_vars="year", value_vars=["arrival_rate_pct", "departure_rate_pct"], var_name="Rate", value_name="Percent")
        rates.Rate = rates.Rate.map({"arrival_rate_pct":"Arrivals / ending electorate", "departure_rate_pct":"Departures / starting electorate"})
        chart(px.line(rates, x="year", y="Percent", color="Rate", markers=True, color_discrete_sequence=[BLUE, ORANGE]))
        st.caption("Rates use different denominators to match the earlier analysis; they cannot be subtracted to calculate a net rate.")

with origins:
    if flows is None:
        st.info("Add belmont_annual_flows_2016_2025.csv to data/ to enable origin filters, rankings and annual trends.")
        st.write("The app will distinguish observed prior NC counties from inferred interstate origins. The full export is needed; the logs only contain a partial ranking.")
    else:
        scoped = filter_years(flows, "cohort_year", selected)
        total = int(view.arrivals.sum())
        mapped = int(scoped.movers.sum())
        st.metric("Arrivals with a classified geographic origin", f"{mapped:,}", f"{mapped / total:.1%} of all arrivals" if total else None, delta_color="off")
        st.warning("Observed NC counties come from prior registrations. Inferred state origins may use birthplace as a proxy and do not establish the previous state of residence. Unmapped arrivals are excluded from these origin charts.")
        confidence = st.multiselect("Evidence", sorted(scoped.origin_confidence.unique()), default=sorted(scoped.origin_confidence.unique()))
        filtered = scoped[scoped.origin_confidence.isin(confidence)]
        choices = sorted(filtered.origin_name.unique())
        names = st.multiselect("Origin locations (blank means all)", choices)
        if names:
            filtered = filtered[filtered.origin_name.isin(names)]
        if filtered.empty:
            st.info("No origins match these filters.")
        else:
            ranking = filtered.groupby(["origin_name", "origin_confidence"], as_index=False).movers.sum()
            top = ranking.sort_values("movers", ascending=False).head(20).sort_values("movers")
            fig = px.bar(top, x="movers", y="origin_name", color="origin_confidence", orientation="h", color_discrete_sequence=[BLUE, ORANGE])
            fig.update_layout(template="plotly_white", xaxis_title="Arrival events", yaxis_title=None)
            st.plotly_chart(fig, use_container_width=True)
            trend = filtered.groupby("cohort_year").movers.sum().reindex(view.year, fill_value=0).rename_axis("year").reset_index()
            chart(px.line(trend, x="year", y="movers", markers=True, color_discrete_sequence=[BLUE]))
            st.dataframe(ranking.sort_values("movers", ascending=False), hide_index=True, use_container_width=True)
            st.download_button("Download filtered origin totals", filtered.to_csv(index=False).encode(), "origin_totals.csv", "text/csv")

with methods:
    st.subheader("Definitions and limitations")
    st.markdown("""
    - **Population:** registered voters classified as Belmont in the source snapshots. Original status and geography rules still need to be confirmed from the source pipeline.
    - **Arrival:** appears in the ending Belmont snapshot, absent from the starting Belmont snapshot. This can include first-time registration, reactivation and residential moves.
    - **Departure:** appears in the starting Belmont snapshot, absent from the ending snapshot. Removal, death and changes in eligibility can contribute alongside moves.
    - **Net registration change:** arrivals minus departures; this is not a population-migration estimate.
    - **Repeat events:** a person can arrive in more than one year. Annual event totals are additive; unique people require the original person-level records.
    - **Origin evidence:** observed prior NC registration and inferred state proxies must remain distinguishable. Birthplace is not previous residence.
    - **Missing features:** destination geography, party/age/precinct breakdowns, multi-year retention and current-electorate cohort composition require additional exports. No illustrative values are substituted.
    """)
    st.caption("Source: belmont_map_coverage_by_year.csv and belmont_annual_flows_2016_2025.csv, downloaded from the supplied ncsbe_migration Drive folder. Both show an August 29 modification date. Coverage counts reconcile exactly with annual origin totals. Enriched files in a separate folder have not yet been integrated.")
    st.dataframe(view, hide_index=True, use_container_width=True)
    st.download_button("Download selected annual data", view.to_csv(index=False).encode(), "annual_data.csv", "text/csv")
