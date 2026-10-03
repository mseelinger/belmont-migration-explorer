"""Aggregate origin maps with comparable widths across animation frames."""
import plotly.graph_objects as go

COLORS={'OBSERVED':'#2878A5','HISTORICAL_OBSERVED':'#238C7C','INFERRED':'#E78A38'}
LABELS={'OBSERVED':'Prior NC registration','HISTORICAL_OBSERVED':'Historical NC evidence','INFERRED':'Inferred state proxy'}
KEYS=['origin_name','origin_confidence','origin_lat','origin_lon','dest_lat','dest_lon']

def migration_map(flows, animate=False, years=None, region='United States'):
    grouped=flows.groupby(KEYS,as_index=False).movers.sum()
    routes=list(grouped.itertuples(index=False))
    if animate:
        maximum=flows.groupby(['cohort_year']+KEYS).movers.sum().max()
    else:
        maximum=grouped.movers.max()
    def traces(frame):
        totals=frame.groupby(KEYS).movers.sum().to_dict()
        result=[]; seen=set()
        for route in routes:
            key=tuple(getattr(route,c) for c in KEYS)
            count=int(totals.get(key,0)); evidence=route.origin_confidence
            result.append(go.Scattergeo(lon=[route.origin_lon,route.dest_lon],lat=[route.origin_lat,route.dest_lat],
                mode='lines',line=dict(width=8*count/maximum if count else 0,color=COLORS.get(evidence,'#697987')),
                opacity=.65 if count else 0, name=LABELS.get(evidence,evidence),legendgroup=evidence,
                showlegend=evidence not in seen,
                text=f'{route.origin_name} → Belmont<br>{count:,} events<br>{LABELS.get(evidence,evidence)}',hoverinfo='text'))
            seen.add(evidence)
        result.append(go.Scattergeo(lon=grouped.origin_lon,lat=grouped.origin_lat,mode='markers',
            marker=dict(size=5,color='#526875'),text=[f'{r.origin_name}: {int(totals.get(tuple(getattr(r,c) for c in KEYS),0)):,} events' for r in routes],hoverinfo='text',showlegend=False))
        result.append(go.Scattergeo(lon=[routes[0].dest_lon],lat=[routes[0].dest_lat],mode='markers+text',
            marker=dict(size=10,color='#203344'),text=['Belmont'],textposition='bottom right',showlegend=False,hoverinfo='text'))
        return result
    sequence=years or sorted(flows.cohort_year.unique())
    fig=go.Figure(data=traces(flows[flows.cohort_year.eq(sequence[0])] if animate else flows))
    if animate:
        fig.frames=[go.Frame(data=traces(flows[flows.cohort_year.eq(y)]),name=str(y)) for y in sequence]
        fig.update_layout(updatemenus=[dict(type='buttons',direction='left',x=0,y=0,buttons=[
            dict(label='▶ Play',method='animate',args=[None,dict(frame=dict(duration=1000,redraw=True),transition=dict(duration=0),fromcurrent=True)]),
            dict(label='Pause',method='animate',args=[[None],dict(frame=dict(duration=0,redraw=True),mode='immediate')])])],
            sliders=[dict(active=0,x=.2,len=.8,y=0,currentvalue=dict(prefix='Cohort year: '),steps=[
                dict(label=str(y),method='animate',args=[[str(y)],dict(mode='immediate',frame=dict(duration=0,redraw=True),transition=dict(duration=0))]) for y in sequence])])
    geo=dict(scope='usa',projection_type='albers usa',showland=True,landcolor='#EDF1F4',showsubunits=True,subunitcolor='white')
    if region=='North Carolina':
        geo.update(scope='north america',projection_type='mercator',lonaxis_range=[-85,-75],lataxis_range=[33,37.5],showcountries=True)
    fig.update_layout(geo=geo,height=540,margin=dict(l=0,r=0,t=0,b=70 if animate else 0),legend=dict(orientation='h',y=1.05),paper_bgcolor='white')
    return fig
