import dash_auth
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import json
from dash import no_update
import numpy as np

from house_utils_app2 import geo_locate_houses_alt, point_in_polygon

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

USERNAME_PASSWORD_PAIRS = [
    ['JamesBond', '007'], ['LouisArmstrong', 'satchmo']
]

app = dash.Dash()
auth = dash_auth.BasicAuth(app, USERNAME_PASSWORD_PAIRS)
server = app.server

# Subset dataframe to show some specific columns in dash web app
lat_center, long_center = 51.5656872, -0.4034499

n, delta, GS, m = 3, 0.0001, 100, 6
geo_coord_str = "Lat: " + str(lat_center) + ", Long: " + str(long_center)

def draw_map(lat_center, long_center, my_col, data = None):
    # Make boxes
    x = [[long_center + (j-1) * 2 * delta - delta, long_center + (j-1) * 2 * delta + delta, long_center + (j-1) * 2 * delta + delta,
          long_center + (j-1) * 2 * delta - delta, long_center + (j-1) * 2 * delta - delta] for j in range(n)]
    y = [[lat_center - delta, lat_center - delta, lat_center + delta, lat_center + delta, lat_center - delta] for j in range(n)]

    fig = go.Figure()
    fig.add_trace(go.Scattermapbox(
            lat=[lat_center],
            lon=[long_center],
            mode='markers',
            marker=go.scattermapbox.Marker(
                size=8,
                color='rgb(255, 0, 0)',
                opacity=0.7
            ),
            hoverinfo='text'
        ))

    if data is not None:
        fig.add_trace(go.Scattermapbox(
            lat=[data[0]],
            lon=[data[1]],
            mode='markers',
            marker=go.scattermapbox.Marker(
                size=8,
                color='rgb(0, 255, 0)',
                opacity=0.7
            ),
            hoverinfo='text'
        ))

    for j in range(len(x)):
        fig.add_trace(go.Scattermapbox(
            mode="markers+lines",
            lon=x[j],
            lat=y[j],
            marker={'size': 10},
            line=dict(color=my_col)))

    fig.add_trace(go.Scattermapbox(
            lat=np.repeat(np.linspace(lat_center-m*delta, lat_center+m*delta, GS), GS),
            lon=np.tile(np.linspace(long_center-m*delta, long_center+m*delta, GS), GS),
            mode='markers',
            marker=go.scattermapbox.Marker(
                size=8,
                color='rgb(0,0,255)',
                opacity=0
            )
        ))

    fig.update_layout(
        autosize=True,
        hovermode='closest',
        showlegend=False,
        height=500,
        width=800,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        mapbox=dict(style="open-street-map", center=dict(lon=long_center, lat=lat_center), zoom=19),
        clickmode='event+select'
    )

    return fig

app = dash.Dash(external_stylesheets=['https://codepen.io/amyoshino/pen/jzXypZ.css'])
app.title = 'Open Street Map'

app.layout = html.Div(
    html.Div([
        html.H1(children='Load Map from Address'),
        html.H3('Enter address: (67 Lynmouth Drive Ruislip HA4 9BY)', style={'paddingRight': '30px'}),
        dcc.Input(id="input_address", type="text", placeholder="",
                  style={'paddingRight': '30px', 'width': 500}),
        html.Button(id='submit_button', n_clicks=0, children='Submit'),
        html.Div(id='print_info', children='*'),

        html.Hr(),
        html.H3('Latitude and Longitude of House:', style={'paddingRight': '30px'}),
        html.H3(id='coords', children=geo_coord_str),

        html.Hr(),
        dcc.Graph(id='MapPlot1', figure=draw_map(lat_center, long_center, "#ff0000")),

        html.Hr(),
        html.Hr(),
        html.P("Coordinate (click on map):"),
        html.Div(id='print_click_coord', children='**'),
    ])
)

@app.callback(
    Output('print_info', 'children'),
    [Input('submit_button', 'n_clicks')],
    [State('input_address', 'value')])
def geolocate_address(n_clicks, input_value):
    if input_value is not None and n_clicks > 0:
        global long_center
        global lat_center
        id_house, house_number, postcode, xt, yt, long_center, lat_center = geo_locate_houses_alt(input_value)
        return 'House id: "{}", House number: "{}", Postcode: "{}", xt: "{}", yt: "{}", xd: "{}", yd: "{}"'.format(id_house, house_number, postcode, xt, yt, long_center, lat_center)
    return no_update

@app.callback(
    Output('coords', 'children'),
    [Input('print_info', 'children')])
def update_lat_long_div(value):
    return "Lat: " + str(lat_center) +", Long: " + str(long_center)

@app.callback(
    Output('MapPlot1', 'figure'),
    [Input('print_info', 'children'),
     Input('MapPlot1', 'clickData')])
def update_map1(value, data):
    if data is not None:
        return draw_map(lat_center, long_center, "#00ffff", [data['points'][0]['lat'], data['points'][0]['lon']])
    return draw_map(lat_center, long_center, "#00ff00")

@app.callback(
    Output('print_click_coord', 'children'),
    [Input('MapPlot1', 'clickData')])
def display_click_data(custom_data):
    print(custom_data)
    if custom_data is not None:
        return "Lat: " + str(custom_data['points'][0]['lat']) +", Long: " + str(custom_data['points'][0]['lon'])
    return no_update

# @app.callback(
#     Output('MapPlot1', 'figure'),
#     [Input('print_click_coord', 'children')])
# def draw_selected_site(coordinates):
#     print(coordinates)
#     return draw_map(lat_center, long_center, "#00ffff")


if __name__ == '__main__':
    app.run_server(debug=True)
