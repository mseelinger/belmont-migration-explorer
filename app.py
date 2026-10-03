from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from model import load_bundle, filter_years
from maps import migration_map, COLORS, LABELS

st.set_page_config(page_title='Belmont Migration Explorer | Tar Heel Tally',page_icon='📊',layout='wide')
DATA=Path(__file__).parent/'data'
if not DATA.exists(): DATA=Path(__file__).parent
BLUE,ORANGE='#2878A5','#E78A38'
st.caption('TAR HEEL TALLY · SNAPSHOTS 2016–2026')
st.title('Belmont Migration Explorer')
st.write('Explore Belmont’s registered electorate: arrivals, departures, origin evidence, and the cohorts still registered here.')
@st.cache_data
def dataset(directory): return load_bundle(Path(directory))
try:
    annual,flows,coverage,profiles,retention,destinations,composition,ranges,metadata=dataset(str(DATA))
except (ValueError,KeyError,OSError) as error:
    st.error(f'Unable to load the dataset: {error}'); st.stop()
years=annual.year.tolist()
with st.sidebar:
    st.header('Explore the data')
    selected=st.select_slider('Years',options=years,value=(years[0],years[-1]))
    st.caption('A cohort year compares January 1 of that year with January 1 of the following year. Only Gaston County / Belmont records with status other than R are included.')
    st.caption(f"{metadata['source_files']} source files integrated · Aggregate data only")
view=filter_years(annual,'year',selected)
scoped=filter_years(flows,'cohort_year',selected)
total=int(view.arrivals.sum()); mapped=int(scoped.movers.sum())
overview,origins,profile_tab,cohorts,methods=st.tabs(['Overview','Origins & maps','Profiles & departures','Cohort retention','Data & methods'])

def chart(fig,annual_axis=False):
    fig.update_layout(template='plotly_white',margin=dict(l=0,r=0,t=25,b=0),legend_title_text='',font=dict(color='#203344'))
    if annual_axis: fig.update_xaxes(dtick=1)
    st.plotly_chart(fig,width='stretch')

def download(label,frame,name):
    st.download_button(label,frame.to_csv(index=False).encode(),name,'text/csv')

with overview:
    stat=ranges[(ranges.start_year.eq(selected[0]))&(ranges.end_year.eq(selected[1]))].iloc[0]
    cards=st.columns(4)
    cards[0].metric('Arrival events',f'{total:,}')
    cards[1].metric('Departure events',f'{view.departures.sum():,}')
    cards[2].metric('Net registration change',f'{view.net_change.sum():+,}')
    cards[3].metric('Unique people arriving',f'{stat.unique_arrivals:,}')
    st.caption('Events are changes in snapshot membership, which can include moves, new registrations, removals, and reactivations. A person may arrive more than once; these are not population migration estimates.')
    st.subheader('Arrivals and departures over time')
    fig=go.Figure(go.Bar(x=view.year,y=view.arrivals,name='Arrivals',marker_color=BLUE))
    fig.add_bar(x=view.year,y=view.departures,name='Departures',marker_color=ORANGE)
    fig.add_scatter(x=view.year,y=view.net_change,name='Net registration change',mode='lines+markers',line=dict(color='#203344'))
    fig.update_layout(barmode='group',yaxis_title='Registration events')
    chart(fig,True)
    st.subheader('Electorate size and turnover')
    year=st.selectbox('Inspect a cohort year',view.year.tolist(),index=len(view)-1)
    row=view[view.year.eq(year)].iloc[0]
    cards=st.columns(4)
    for col,label,value in zip(cards,['Starting electorate','Ending electorate','Net registration change','One-period retention'],[f'{row.start_voters:,.0f}',f'{row.end_voters:,.0f}',f'{row.net_change:+,.0f}',f'{row.retention_rate_pct:.1f}%']): col.metric(label,value)
    st.caption(f'{year}-01-01 → {year+1}-01-01. One-period retention = present in both snapshots ÷ starting electorate.')
    stocks=pd.DataFrame({'Snapshot year':[int(view.iloc[0].year)]+(view.year+1).tolist(),'Registered voters':[int(view.iloc[0].start_voters)]+view.end_voters.tolist()})
    chart(px.line(stocks,x='Snapshot year',y='Registered voters',markers=True,color_discrete_sequence=[BLUE]),True)
    rates=view.melt(id_vars='year',value_vars=['arrival_rate_pct','departure_rate_pct'],var_name='Rate',value_name='Percent')
    rates.Rate=rates.Rate.map({'arrival_rate_pct':'Arrivals / ending electorate','departure_rate_pct':'Departures / starting electorate'})
    chart(px.line(rates,x='year',y='Percent',color='Rate',markers=True,color_discrete_sequence=[BLUE,ORANGE]),True)
    st.caption('These rates have different denominators and cannot be subtracted to calculate a net rate.')

with origins:
    cards=st.columns(3)
    cards[0].metric('Geographic origin assigned',f'{mapped:,}',f'{mapped/total:.1%} of arrivals',delta_color='off')
    cards[1].metric('Unmapped arrivals',f'{total-mapped:,}')
    original=pd.read_csv(DATA/'belmont_map_coverage_by_year.csv')
    old=int(filter_years(original,'cohort_year',selected).mapped_arrivals.sum())
    cards[2].metric('Additional origins after enrichment',f'{mapped-old:+,}')
    st.warning('Prior NC registration is observed evidence. Historical registration/voting evidence may be older. Inferred state origins use birthplace as a proxy; none of these categories alone proves the immediately previous residence.')
    evidence=st.multiselect('Evidence',list(LABELS),default=list(LABELS),format_func=lambda v:LABELS[v])
    filtered=scoped[scoped.origin_confidence.isin(evidence)]
    names=st.multiselect('Origin locations (blank means all)',sorted(filtered.origin_name.unique()))
    if names: filtered=filtered[filtered.origin_name.isin(names)]
    st.caption(f'{int(filtered.movers.sum()):,} arrival events match the origin filters. Coverage above is calculated before these filters.')
    if filtered.empty:
        st.info('No origins match these filters.')
    else:
        left,right=st.columns(2)
        mode=left.radio('Map period',['Selected years combined','Animate annual cohorts'],horizontal=True)
        region=right.radio('Map view',['United States','North Carolina'],horizontal=True)
        st.plotly_chart(migration_map(filtered,animate=mode=='Animate annual cohorts',years=view.year.tolist(),region=region),width='stretch',key='migration_map')
        st.caption('Lines connect county/state centroids to Belmont. Width is proportional to arrival events; annual animation uses a fixed scale across years. Unmapped arrivals are excluded. The NC view clips origins outside the displayed region.')
        ranking=filtered.groupby(['origin_name','origin_confidence'],as_index=False).movers.sum()
        top_names=ranking.groupby('origin_name').movers.sum().nlargest(20).index
        top=ranking[ranking.origin_name.isin(top_names)].copy(); top['Evidence']=top.origin_confidence.map(LABELS)
        fig=px.bar(top,x='movers',y='origin_name',color='Evidence',orientation='h',color_discrete_map={LABELS[k]:v for k,v in COLORS.items()})
        fig.update_layout(yaxis=dict(categoryorder='total ascending'),xaxis_title='Arrival events',yaxis_title=None,height=600)
        chart(fig)
        trend=filtered.groupby(['cohort_year','origin_confidence']).movers.sum().unstack(fill_value=0).reindex(view.year,fill_value=0).fillna(0).rename_axis('year').reset_index()
        trend=trend.melt(id_vars='year',var_name='Evidence',value_name='Arrival events'); trend.Evidence=trend.Evidence.map(LABELS)
        chart(px.line(trend,x='year',y='Arrival events',color='Evidence',markers=True,color_discrete_map={LABELS[k]:v for k,v in COLORS.items()}),True)
        st.dataframe(ranking.sort_values('movers',ascending=False),hide_index=True,width='stretch')
        download('Download filtered origin totals',filtered,'origin_totals.csv')

with profile_tab:
    st.subheader('Who appears in the snapshots?')
    population=st.radio('Population',['Arrivals','Departures','Ending electorate'],horizontal=True)
    available=sorted(profiles.loc[profiles.population.eq(population),'dimension'].unique())
    dimension=st.selectbox('Breakdown',available,index=available.index('Party'))
    p=filter_years(profiles,'year',selected)
    p=p[p.population.eq(population)&p.dimension.eq(dimension)].copy()
    if population=='Ending electorate':
        snapshot=st.selectbox('Ending snapshot cohort year',view.year.tolist(),index=len(view)-1)
        p=p[p.year.eq(snapshot)]
        st.caption(f'Electorate present on January 1, {snapshot+1}. Electorate stocks are shown one snapshot at a time.')
    elif population=='Departures':
        st.caption('Profile fields come from each departure’s starting snapshot.')
    else:
        st.caption('Profile fields come from each arrival’s ending snapshot; ages outside 16–110 are grouped as unknown / invalid.')
    grouped=p.groupby('category',as_index=False).events.sum().sort_values('events',ascending=False)
    grouped['Share (%)']=100*grouped.events/grouped.events.sum()
    chart(px.bar(grouped,x='events',y='category',orientation='h',color_discrete_sequence=[BLUE]).update_layout(yaxis=dict(categoryorder='total ascending'),xaxis_title='Voters' if population=='Ending electorate' else 'Events',yaxis_title=None))
    st.dataframe(grouped,hide_index=True,width='stretch')
    download('Download selected profile',p,'profile_totals.csv')
    st.subheader('What appears after a departure?')
    st.caption('These are ending-snapshot registration locations, not confirmed residential destinations. Removed-only and absent records can reflect death, cancellation, or other changes, as well as moves.')
    dest=filter_years(destinations,'year',selected)
    dt=dest.groupby(['destination','evidence'],as_index=False).events.sum().sort_values('events',ascending=False)
    st.dataframe(dt,hide_index=True,width='stretch')
    download('Download departure evidence',dest,'departure_evidence.csv')

with cohorts:
    st.subheader('Arrival cohorts over time')
    st.write('Follow each annual arrival cohort through later January 1 snapshots. People who depart and return count as present again, while continuous presence remains broken.')
    measure=st.radio('Retention measure',['Present at each snapshot','Continuously present'],horizontal=True)
    r=filter_years(retention,'cohort_year',selected)
    column='present' if measure=='Present at each snapshot' else 'continuously_present'
    r['Retention (%)']=100*r[column]/r.cohort_size
    r['Cohort']=r.cohort_year.astype(str)
    chart(px.line(r,x='years_since_arrival',y='Retention (%)',color='Cohort',markers=True).update_layout(xaxis_title='Years since arrival snapshot',yaxis=dict(range=[0,105])))
    st.caption('Year 0 is the ending snapshot that identifies the arrival. Continuous presence means present in every observed annual snapshot; changes between snapshots cannot be detected. Recent cohorts have shorter follow-up.')
    heat=r.pivot(index='cohort_year',columns='snapshot_year',values='Retention (%)')
    chart(px.imshow(heat,text_auto='.1f',color_continuous_scale='Blues',zmin=0,zmax=100,labels=dict(x='January 1 snapshot',y='Arrival cohort',color='Retention (%)'),aspect='auto'))
    download('Download cohort retention',r.drop(columns=['Cohort']),'cohort_retention.csv')
    st.subheader('Composition of the January 1, 2026 electorate')
    st.caption('Each currently registered voter is assigned to their latest observed arrival spell, or to Before 2016 if no later re-entry was observed. This fixed snapshot is independent of the sidebar range.')
    c=composition.copy(); c['Share (%)']=100*c.voters/c.voters.sum()
    chart(px.bar(c,x='arrival_cohort',y='voters',color_discrete_sequence=[BLUE]).update_layout(xaxis_title='Latest arrival cohort',yaxis_title='Registered voters',xaxis_type='category'))
    st.dataframe(c,hide_index=True,width='stretch')
    download('Download 2026 electorate composition',c,'electorate_composition_2026.csv')

with methods:
    st.subheader('Sources and reconciliation')
    st.success(f"Integrated {metadata['source_files']} source files: all 11 annual snapshots and 64 output, validation, mapping and cache files. Final enriched exports supply origin evidence; intermediate caches are audit inputs and are not added to the totals.")
    for note in metadata['quality_notes']: st.info(note)
    st.markdown('''
- **Population:** `county_desc = GASTON`, `municipality_desc = BELMONT`, and `status_cd != R`. The municipality field defines the boundary; a Belmont mailing city alone is insufficient. Active, inactive and other non-removed statuses are included.
- **Arrival / departure:** set differences of NC voter identifiers between consecutive January 1 Belmont snapshots. An arrival can be new registration, reactivation, or a move. A departure can be removal, death, a move, or a geography/status change.
- **Reconciliation:** starting electorate − departures = retained; retained + arrivals = ending electorate. Each year's arrival identifiers agree exactly with the enriched person export and validation counts.
- **Unique arrivals:** distinct identifiers within the selected years, calculated before publishing aggregates. A repeat arrival contributes multiple events but one unique person.
- **Origin evidence:** observed prior NC registrations, historical NC registration/voting clues, and inferred birthplace proxies are kept separate. Historical evidence is not proof of the immediately previous residence.
- **Profiles:** arrival fields use the ending snapshot; departure fields use the starting snapshot. Registration timing is source metadata and does not independently establish a move date. Party and demographic codes are shown as supplied; unknown values remain visible.
- **Privacy:** the public repository and downloads contain counts and centroid coordinates, with no individual names, identifiers, residential addresses, or voter histories.
- **Interpretation:** registered-electorate changes are not estimates of total population migration. Snapshot filenames and stored dates establish comparison dates; the original raw extraction pipeline is not included in the folder.
''')
    st.subheader('Annual data')
    st.dataframe(view,hide_index=True,width='stretch'); download('Download selected annual data',view,'annual_data.csv')
    cv=filter_years(coverage,'cohort_year',selected)
    st.subheader('Origin coverage'); st.dataframe(cv,hide_index=True,width='stretch'); download('Download origin coverage',cv,'origin_coverage.csv')
    validation=pd.read_csv(DATA/'arrival_validation.csv')
    st.subheader('Prior snapshot validation'); st.dataframe(filter_years(validation,'year',selected),hide_index=True,width='stretch')
    with st.expander('Source file inventory and checksums'):
        inventory=pd.read_csv(DATA/'source_inventory.csv')
        st.dataframe(inventory,hide_index=True,width='stretch'); download('Download source inventory',inventory,'source_inventory.csv')
    st.caption('Source: the supplied ncsbe_migration Google Drive folder. Aggregates generated October 3, 2026. Reproduce with prepare_data.py against a local copy of the source folder.')
