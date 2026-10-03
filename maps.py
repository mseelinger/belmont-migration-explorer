"""Aggregate origin maps with comparable widths across animation frames."""
import plotly.graph_objects as go
import numpy as np

COLORS={'OBSERVED':'#2878A5','HISTORICAL_OBSERVED':'#238C7C','INFERRED':'#E78A38'}
DARK_COLORS={'OBSERVED':'#155A85','INFERRED':'#B95409'}
LIGHT_COLORS={'OBSERVED':'#BAD5E7','INFERRED':'#F4DCC3','HISTORICAL_OBSERVED':'#C4E1DC'}
LABELS={'OBSERVED':'Prior NC registration','HISTORICAL_OBSERVED':'Historical NC evidence','INFERRED':'Inferred state proxy'}
KEYS=['origin_name','origin_confidence','origin_lat','origin_lon','dest_lat','dest_lon']

def line_width(count):
    if count == 0: return 0
    for upper, width in [(10,1),(50,2.5),(200,5),(1000,9)]:
        if count <= upper: return width
    return 15


def route_points(origin_lat, origin_lon, dest_lat, dest_lon):
    # Dense great-circle points let Plotly detect hover along the entire line.
    lat, lon = np.radians([origin_lat,dest_lat]), np.radians([origin_lon,dest_lon])
    vectors=np.column_stack([np.cos(lat)*np.cos(lon),np.cos(lat)*np.sin(lon),np.sin(lat)])
    angle=np.arccos(np.clip(np.dot(*vectors),-1,1))
    t=np.linspace(0,1,240)
    if angle<1e-9: points=np.repeat(vectors[:1],len(t),axis=0)
    else: points=(np.sin((1-t)*angle)[:,None]*vectors[0]+np.sin(t*angle)[:,None]*vectors[1])/np.sin(angle)
    return np.degrees(np.arctan2(points[:,1],points[:,0])),np.degrees(np.arctan2(points[:,2],np.hypot(points[:,0],points[:,1])))


def migration_map(flows, animate=False, years=None, region='United States'):
    grouped=flows.groupby(KEYS,as_index=False).movers.sum()
    routes=list(grouped.sort_values('movers').itertuples(index=False))
    def traces(frame):
        totals=frame.groupby(KEYS).movers.sum().to_dict()
        highlighted=set()
        for evidence in DARK_COLORS:
            ranked=sorted(((key,count) for key,count in totals.items() if key[1]==evidence and count>0),key=lambda item:(-item[1],item[0][0]))
            highlighted.update(key for key,count in ranked[:10])
        def route_color(key):
            return DARK_COLORS[key[1]] if key in highlighted else LIGHT_COLORS.get(key[1],'#D8E0E5')
        result=[]; seen=set()
        for route in routes:
            key=tuple(getattr(route,c) for c in KEYS)
            count=int(totals.get(key,0)); evidence=route.origin_confidence
            lon,lat=route_points(route.origin_lat,route.origin_lon,route.dest_lat,route.dest_lon)
            result.append(go.Scattergeo(lon=lon,lat=lat,
                mode='lines',line=dict(width=line_width(count),color=route_color(key)),
                opacity=.95 if count else 0, name=LABELS.get(evidence,evidence),legendgroup=evidence,
                showlegend=evidence not in seen,
                text=[f'{route.origin_name} → Belmont<br>Arrivals: {count:,}<br>{LABELS.get(evidence,evidence)}']*len(lon),hovertemplate='%{text}<extra></extra>'))
            seen.add(evidence)
        result.append(go.Scattergeo(lon=[r.origin_lon for r in routes],lat=[r.origin_lat for r in routes],mode='markers',
            marker=dict(size=[5 if totals.get(tuple(getattr(r,c) for c in KEYS),0) else 0 for r in routes],color=[route_color(tuple(getattr(r,c) for c in KEYS)) for r in routes]),text=[f'{r.origin_name}: {int(totals.get(tuple(getattr(r,c) for c in KEYS),0)):,} arrivals' for r in routes],hoverinfo='text',showlegend=False))
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
    fig.update_layout(hovermode='closest',hoverdistance=12,geo=geo,height=540,margin=dict(l=0,r=0,t=0,b=70 if animate else 0),legend=dict(orientation='h',y=1.05),paper_bgcolor='white')
    return fig
