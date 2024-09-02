import os
import networkx as nx
import numpy as np
from pathlib import Path
import sys

from dash import Dash, dcc, html, callback, Output, Input, State, ctx, no_update
from src.tonality_distance import get_tonality_distance
from src.music_theory import *
import plotly.express as px
import plotly.graph_objects as go

edge_color_dict = {'Neighbor':'blue','Relative':'green','Parallel':'red','Dominant':'purple','Enharmonic':'orange'}

x = []
y = []
text = []
text_color = []
annotations = []
custom_data = []

for diatonic in range(7):
    for chromatic in range(12):
        pitch = Pitch.from_dia_chro(diatonic,chromatic)

        x.append(chromatic)
        y.append(diatonic)

        x.append(chromatic+0.3)
        y.append(diatonic)

        text_color.append('blue')
        text_color.append('red')

        if len(pitch.accidental)<=1 :
            text.append(f'{pitch.name}')
            text.append(f'{pitch.name.lower()}')
        else:
            text.append(f'\u25EF')
            text.append(f'\u25EF')

        annotations.append(f'{pitch.name}')
        annotations.append(f'{pitch.name.lower()}')
        custom_data.append((diatonic,chromatic,'M'))
        custom_data.append((diatonic,chromatic,'m'))

text_trace = go.Scatter(x = x, y = y,
                    mode = 'text',
                    text = text,
                    textfont= dict(size = 16, color = text_color),
                    hoverinfo = 'skip',
                    showlegend=False)
invis_node = go.Scatter(x = x, y = y,
                        mode = 'markers',
                        text = annotations,
                        hoverinfo = 'text',
                        marker= dict(color = text_color),
                        opacity=0,
                        customdata=custom_data,
                        showlegend=False)

fig = go.Figure()
fig.add_trace(text_trace)
fig.add_trace(invis_node)
fig.update_layout(showlegend=True)

keys = []
for dia in range(7):
    for chro in range(12):
        for mode in ['m','M']:
            pitch = Pitch.from_dia_chro(dia,chro)
            keys.append(f'{pitch.name if mode == "M" else pitch.name.lower()}')
keys = sorted(keys, key = lambda x: (len(x),x))

default_neighbor_weight = 1
default_relative_weight = 0.7
default_parallel_weight = 1.3
default_enharmonic_weight = 0.01
default_dominant_weight = 1.2

app = Dash(__name__)
app.title = 'Tonality distance calculator'
app.layout = [
    html.H1('Tonality distance calculator'),
    html.Div([
        html.H2('Modulation weight settings'),
        html.Div([
            html.Div([
                dcc.Checklist(['Neighbor weight:'], ['Neighbor weight:'], id = 'neighbor_weight_checklist'),
                dcc.Slider(id='neighbor_weight', min=0.01, max=10, step=0.1, value=default_neighbor_weight,
                           tooltip={"placement": "bottom"},
                           marks = {i:str(i) for i in sorted([0.01,1,2,5,10])}),
            ]),
            html.Div([
                dcc.Checklist(['Relative weight:'], ['Relative weight:'], id = 'relative_weight_checklist'),
                dcc.Slider(id='relative_weight', min=0.01, max=10, step=0.1, value=default_relative_weight,
                           tooltip={"placement": "bottom"},
                           marks = {i:str(i) for i in sorted([0.01,1,2,5,10])}),
            ]),
            html.Div([
                dcc.Checklist(['Parallel weight:'], ['Parallel weight:'], id = 'parallel_weight_checklist'),
                dcc.Slider(id='parallel_weight', min=0.01, max=10, step=0.1, value=default_parallel_weight,
                           tooltip={"placement": "bottom"},
                           marks = {i:str(i) for i in sorted([0.01,1,2,5,10])}),
            ]),
            html.Div([
                dcc.Checklist(['Enharmonic weight:'], ['Enharmonic weight:'], id = 'enharmonic_weight_checklist'),
                dcc.Slider(id='enharmonic_weight', min=0.01, max=10, step=0.1, value=default_enharmonic_weight,
                           tooltip={"placement": "bottom"},
                           marks = {i:str(i) for i in sorted([0.01,1,2,5,10])}),
            ]),
            html.Div([
                dcc.Checklist(['Dominant weight:'], ['Dominant weight:'], id = 'dominant_weight_checklist'),
                dcc.Slider(id='dominant_weight', min=0.01, max=10, step=0.1, value=default_dominant_weight,
                           tooltip={"placement": "bottom"},
                           marks = {i:str(i) for i in sorted([0.01,1,2,5,10])}),
            ]),
            html.Button('Default weights', id='clear_weight_button', n_clicks=0),
        ])
    ]),
    html.Div([
        html.H2('Select keys or click on the graph'),
        dcc.Dropdown(id='key_selected',multi=True,options = keys),
        html.Button('Clear selection', id='clear_button', n_clicks=0),
        dcc.Graph(id='keys_graph', figure=fig),
        html.Div(id='output'),
        dcc.RadioItems(id='shortest_path_selector',options=[]),
        html.Div(id='shortest_path_descr'),
    ]),

]

@callback(
    Output('neighbor_weight', 'value'),
    Output('relative_weight', 'value'),
    Output('parallel_weight', 'value'),
    Output('enharmonic_weight', 'value'),
    Output('dominant_weight', 'value'),
    Input('clear_weight_button', 'n_clicks'),
)
def clear_weights(n_clicks):
    return default_neighbor_weight, default_relative_weight, default_parallel_weight, default_enharmonic_weight, default_dominant_weight

@callback(
    Output('key_selected', 'value', allow_duplicate=True),
    Input('clear_button', 'n_clicks'),
    prevent_initial_call=True
)
def clear_keys(n_clicks):
    return []

@callback(
    Output('key_selected', 'value'),
    Input('keys_graph', 'clickData'),
    State('key_selected', 'value'),
)
def select_key(clickData, key_selected):

    if key_selected is None:
        key_selected = []

    if clickData is None:
        return key_selected
    # click_text = clickData['points'][0]['text']
    # if click_text.lower() == click_text:
    #     mode = 'm'
    # else:
    #     mode = 'M'
    # pitch = Pitch.from_name(click_text.upper())
    diatonic, chromatic, mode = clickData['points'][0]['customdata']
    pitch = Pitch.from_dia_chro(diatonic,chromatic)
    pitch_name = pitch.name if mode == 'M' else pitch.name.lower()
    if len(key_selected) >= 2:
        return key_selected[:1]+[pitch_name]
    return key_selected+[pitch_name]

@callback(
    Output('keys_graph', 'figure', allow_duplicate=True),
    Output('output', 'children'),
    Output('shortest_path_descr', 'children'),
    Output('shortest_path_selector', 'options'),
    Output('shortest_path_selector', 'value'),
    Input('key_selected', 'value'),
    Input('neighbor_weight', 'value'),
    Input('relative_weight', 'value'),
    Input('parallel_weight', 'value'),
    Input('enharmonic_weight', 'value'),
    Input('dominant_weight', 'value'),
    Input('neighbor_weight_checklist', 'value'),
    Input('relative_weight_checklist', 'value'),
    Input('parallel_weight_checklist', 'value'),
    Input('enharmonic_weight_checklist', 'value'),
    Input('dominant_weight_checklist', 'value'),
    prevent_initial_call=True
)
def update_keys_graph(key_selected,
                      neighbor_weight, relative_weight, parallel_weight, enharmonic_weight, dominant_weight,
                      neighbor_present, relative_present, parallel_present, enharmonic_present, dominant_present):
    neighbor_weight = neighbor_weight if neighbor_present else np.inf
    relative_weight = relative_weight if relative_present else np.inf
    parallel_weight = parallel_weight if parallel_present else np.inf
    enharmonic_weight = enharmonic_weight if enharmonic_present else np.inf
    dominant_weight = dominant_weight if dominant_present else np.inf
    output_text = ''
    fig = go.Figure()
    fig.add_trace(text_trace)
    fig.add_trace(invis_node)
    fig.update_layout(showlegend=True)
    options = []
    value = -1
    if len(key_selected) >= 1:
        tonality_distance, keys_graph = get_tonality_distance(neighbor_weight, relative_weight, parallel_weight, enharmonic_weight, dominant_weight)
        start_pitch=Pitch(key_selected[0].upper())
        start_mode = 'M' if key_selected[0].isupper() else 'm'
        new_annotations = []
        weights = []
        text_colors = []
        for diatonic in range(7):
            for chromatic in range(12):
                pitch = Pitch.from_dia_chro(diatonic,chromatic)
                interval = Interval(start_pitch, pitch)
                for mode in ['M','m']:
                    shortest_path = nx.shortest_path(keys_graph,(start_pitch.diatonic,start_pitch.chromatic,start_mode),(diatonic,chromatic,mode),weight='weight')
                    distance = tonality_distance[interval.diatonic,interval.chromatic,2*int(start_mode == 'm')+int(mode=='m')]
                    pitch_name = pitch.name if mode == 'M' else pitch.name.lower()
                    new_annotations.append(f'{pitch_name}<br>'\
                                           f'Distance from {key_selected[0]}: {distance}<br>'\
                                           f'Shortest path: {shortest_path}')

                    if key_selected[0]==pitch_name or (len(key_selected)==2 and key_selected[1]==pitch_name):
                        weights.append('bold')
                        if mode == 'M':
                            text_colors.append('rgba(0,0,255,1)')
                        else:
                            text_colors.append('rgba(255,0,0,1)')
                    else:
                        weights.append('normal')
                        if mode == 'M':
                            text_colors.append('rgba(0,0,255,0.5)')
                        else:
                            text_colors.append('rgba(255,0,0,0.5)')

        fig.update_traces(textfont = dict(weight=weights, color=text_colors),selector = dict(mode='text'))

        if len(key_selected) == 2:
            end_pitch=Pitch(key_selected[1].upper())
            end_mode = 'M' if key_selected[1].isupper() else 'm'
            all_shortest_paths = list(nx.all_shortest_paths(keys_graph,(start_pitch.diatonic,start_pitch.chromatic,start_mode),(end_pitch.diatonic,end_pitch.chromatic,end_mode),weight='weight'))
            length = nx.shortest_path_length(keys_graph,(start_pitch.diatonic,start_pitch.chromatic,start_mode),(end_pitch.diatonic,end_pitch.chromatic,end_mode),weight='weight')
            output_text = [f'There are {len(list(all_shortest_paths))} shortest paths from {key_selected[0]} to {key_selected[1]} (Total distance: {length:.1f})', html.Br()]
            options = [{'label':f'Shortest path n°{i+1}', 'value':i} for i in range(len(all_shortest_paths))]
            value = 0
    else:
        new_annotations = annotations

    fig.update_traces(text=new_annotations , selector = dict(mode='markers'))
    return fig, output_text, '', options, value

@callback(
    Output('keys_graph', 'figure', allow_duplicate=True),
    Output('shortest_path_descr', 'children', allow_duplicate=True),
    Input('shortest_path_selector', 'value'),
    Input('neighbor_weight', 'value'),
    Input('relative_weight', 'value'),
    Input('parallel_weight', 'value'),
    Input('enharmonic_weight', 'value'),
    Input('dominant_weight', 'value'),
    Input('neighbor_weight_checklist', 'value'),
    Input('relative_weight_checklist', 'value'),
    Input('parallel_weight_checklist', 'value'),
    Input('enharmonic_weight_checklist', 'value'),
    Input('dominant_weight_checklist', 'value'),
    State('key_selected', 'value'),
    prevent_initial_call=True
)
def plot_shortest_path(shortest_path_index, neighbor_weight, relative_weight, parallel_weight, enharmonic_weight, dominant_weight,
                       neighbor_present, relative_present, parallel_present, enharmonic_present, dominant_present, key_selected):
    neighbor_weight = neighbor_weight if neighbor_present else np.inf
    relative_weight = relative_weight if relative_present else np.inf
    parallel_weight = parallel_weight if parallel_present else np.inf
    enharmonic_weight = enharmonic_weight if enharmonic_present else np.inf
    dominant_weight = dominant_weight if dominant_present else np.inf
    if shortest_path_index is None or shortest_path_index == -1 or len(key_selected) < 2:
        return no_update

    fig = go.Figure()
    fig.add_trace(text_trace)
    fig.add_trace(invis_node)
    fig.update_layout(showlegend=True)

    tonality_distance, keys_graph = get_tonality_distance(neighbor_weight, relative_weight, parallel_weight, enharmonic_weight, dominant_weight)
    start_pitch=Pitch(key_selected[0].upper())
    start_mode = 'M' if key_selected[0].isupper() else 'm'
    end_pitch=Pitch(key_selected[1].upper())
    end_mode = 'M' if key_selected[1].isupper() else 'm'
    new_annotations = []
    weights = []
    text_colors = []
    for diatonic in range(7):
        for chromatic in range(12):
            pitch = Pitch.from_dia_chro(diatonic,chromatic)
            interval = Interval(start_pitch, pitch)
            for mode in ['M','m']:
                shortest_path = nx.shortest_path(keys_graph,(start_pitch.diatonic,start_pitch.chromatic,start_mode),(diatonic,chromatic,mode),weight='weight')
                distance = tonality_distance[interval.diatonic,interval.chromatic,2*int(start_mode == 'm')+int(mode=='m')]
                pitch_name = pitch.name if mode == 'M' else pitch.name.lower()
                new_annotations.append(f'{pitch_name}<br>'\
                                        f'Distance from {key_selected[0]}: {distance}<br>'\
                                        f'Shortest path: {shortest_path}')

                if key_selected[0]==pitch_name or (len(key_selected)==2 and key_selected[1]==pitch_name):
                    weights.append('bold')
                    if mode == 'M':
                        text_colors.append('rgba(0,0,255,1)')
                    else:
                        text_colors.append('rgba(255,0,0,1)')
                else:
                    weights.append('normal')
                    if mode == 'M':
                        text_colors.append('rgba(0,0,255,0.5)')
                    else:
                        text_colors.append('rgba(255,0,0,0.5)')

    fig.update_traces(textfont = dict(weight=weights, color=text_colors),selector = dict(mode='text'))

    all_shortest_paths = list(nx.all_shortest_paths(keys_graph,(start_pitch.diatonic,start_pitch.chromatic,start_mode),(end_pitch.diatonic,end_pitch.chromatic,end_mode),weight='weight'))
    length = nx.shortest_path_length(keys_graph,(start_pitch.diatonic,start_pitch.chromatic,start_mode),(end_pitch.diatonic,end_pitch.chromatic,end_mode),weight='weight')
    shortest_path = all_shortest_paths[shortest_path_index]
    output_text = [html.Br()]
    modulation_descr_names = set()
    for i in range(len(shortest_path)-1):
        u = shortest_path[i]
        v = shortest_path[i+1]
        u_pitch = Pitch.from_dia_chro(u[0],u[1])
        v_pitch = Pitch.from_dia_chro(v[0],v[1])
        modulation_descr = keys_graph[u][v]['modulation']
        distance = keys_graph[u][v]['weight']
        length += distance
        fig.add_trace(go.Scatter(
            x = [u_pitch.chromatic+(0.3 if u[2]=='m' else 0), v_pitch.chromatic+(0.3 if v[2]=='m' else 0)],
            y = [u_pitch.diatonic, v_pitch.diatonic],
            mode = 'lines+markers',
            line = dict(width=2, color = edge_color_dict[modulation_descr.split(' ')[0]],),
            marker= dict(symbol= "arrow-bar-up", angleref="previous"),
            hoverinfo = 'skip',
            name = modulation_descr,
            showlegend=modulation_descr not in modulation_descr_names
        ))
        modulation_descr_names.add(modulation_descr)
        output_text.append(html.Br())
        output_text.append(f'{u_pitch.name if u[2] == "M" else u_pitch.name.lower()} -> {v_pitch.name if v[2] == "M" else v_pitch.name.lower()} : {modulation_descr}')
        output_text.append(f' (distance : {distance})')
    return fig, output_text

if __name__ == '__main__':
    app.run(debug=False, port=8051)
