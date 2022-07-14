from dash import Dash
import dash
import dash as dcc, html
from dash.dependencies import Input, Output
from dash import Dash, dcc, html, dcc, Input, Output, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash import dash_table
import plotly.graph_objects as go
import pickle
import pandas as pd
import random

import sys

import argparse
if  __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", help="data csv file")
    parser.add_argument("--clips", help="clip file, should be a pickled dictionary with key being numbers of entries in a clip and values being the indices of the last element of the clip consistent with the data csv file")
    parser.add_argument("--output", help="name of output file, if exists, will append to, otherwise will create")
    parser.add_argument("--irr", help="output file from previous run for reliability")
    args = parser.parse_args()
    df = pd.read_csv(args.data, index_col='semantic_event_id')
    if args.irr and args.clips:
        raise ValueError('You cannot specify both clips and irr')
    if args.irr:
        clips = pd.read_csv(args.irr, names=['semantic_event_id', 'gaming', 'size']).set_index('semantic_event_id')
        irr = True
    else:
        clips = pickle.load(open(args.clips, 'rb'))
        irr = False
    if args.output:
        outfile = args.output
    else:
        outfile = 'output_'+args.data
    if irr:
        outfile = 'irr_'+outfile

columns = ['problem_id', 'goalnode_id', 'Input', 'tutor_outcome', 'attempt', 'duration', 'skill', 'pknown', 'help_level']
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
res = pd.DataFrame([], columns=['gaming'])
app = Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = html.Div([
    
    html.Button('Get new clip', id='serve', n_clicks=0),
    dash_table.DataTable(df[:10][columns].to_dict('records'), 
                         [{"name": i, "id": i} for i in df[columns].columns]
                         , id='rowData'),
    html.Button('Gaming', id='gaming', n_clicks=0),
    html.Button('Not Gaming', id='not_g', n_clicks=0),
    html.Button('Flag', id='flag', n_clicks=0),
    html.Div(id='blank')

])

@app.callback(
    Output('rowData', 'data'),
    Input('serve', 'n_clicks'))
def serve_clip(n_clicks):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if 'serve.n_clicks' in changed_id:
        global k, l
        if len(clips)==0:
            return None
        if irr:
            row = clips.iloc[0]
            l = int(row.size)
            k = row.name
        else:
            for KEY, VALUE in clips.items():
                if len(VALUE)==0:
                    del clips[KEY]
            l = random.choice(list(clips.keys()))
            k = random.choice(list(clips[l]))
        return df[columns].loc[:k].tail(l).to_dict('records')

@app.callback(
    Output('blank', 'children'),
    Input('gaming', 'n_clicks'),
    Input('not_g', 'n_clicks'),
    Input('serve', 'n_clicks'),
    Input('flag', 'n_clicks'))
def record_clip(gaming_click, not_gaming_click, serve_clicks, flag):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    states = {'gaming.n_clicks':1,
              'not_g.n_clicks':0, 
              'flag.n_clicks':-1}
    for state, state_value in states.items():
        if state in changed_id:
            res = pd.DataFrame([], columns=['gaming', 'size'])
            res.loc[k, 'gaming'] = state_value
            res.loc[k, 'size'] = int(l)
            res.to_csv(outfile, mode='a', header=False)
            if not irr:
                clips[l].remove(k)
            else:
                clips.drop(k, inplace=True)
            return 'Success'
    if 'serve.n_clicks' in changed_id:
        return ''



app.run_server(port=8082)