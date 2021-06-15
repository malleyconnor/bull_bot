import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from IPython.display import display, HTML
from dash.dependencies import Input, Output, State
import requests
import json
import pandas as pd

# TODO: Change to CSS
from BullColors import colors
from BullScreener import BullScreener
from BullGraph import *
import rh_interface

from webull import webull







wb = webull()
##wb.login(input('email: '), input('Password: '), 'Conbob', sq[0]['questionId'], input(sq[0]['questionName']))
wbaccount = wb.get_account()

fh = open('webull_credentials.json', 'r')
credential_data = json.load(fh)
fh.close()

wb._refresh_token = credential_data['refreshToken']
wb._access_token = credential_data['accessToken']
wb._token_expire = credential_data['tokenExpireTime']
wb._uuid = credential_data['uuid']

n_data = wb.refresh_login()

credential_data['refreshToken'] = n_data['refreshToken']
credential_data['accessToken'] = n_data['accessToken']
credential_data['tokenExpireTime'] = n_data['tokenExpireTime']

file = open('webull_credentials.json', 'w')
json.dump(credential_data, file)
file.close()

# Initializing webull position data
############################################
wb.get_account_id()
wbaccount = wb.get_account()
wbcolumns = [
    {'name' : 'Ticker', 'id' : 'wbticker'},
    {'name' : 'Name', 'id' : 'wbname'},
    {'name' : 'Shares', 'id' : 'wbshares'},
    {'name' : 'Price', 'id' : 'wbprice'},
    {'name' : 'Net Value', 'id' : 'wbnetvalue'},
    {'name' : 'Unrealized Profit', 'id' : 'wbunrealizedprofitloss'}
]
wbtickers, wbnames, wbshares, wbprices, wbnetvalues, wbunrealizedprofits = [], [], [], [], [], []
for i in range(len(wbaccount['positions'])):
    wbtickers.append(wbaccount['positions'][i]['ticker']['symbol'])
    wbnames.append(wbaccount['positions'][i]['ticker']['tinyName'])
    wbshares.append(wbaccount['positions'][i]['position'])
    wbprices.append(wbaccount['positions'][i]['lastPrice'])
    wbnetvalues.append(wbaccount['positions'][i]['marketValue'])
    wbunrealizedprofits.append(wbaccount['positions'][i]['unrealizedProfitLoss'])
wbdata = {
    'wbticker' : wbtickers,
    'wbname' : wbnames,
    'wbshares' : wbshares,
    'wbprice' : wbprices,
    'wbnetvalue' : wbnetvalues,
    'wbunrealizedprofitloss' : wbunrealizedprofits
}
wb_ticker_list = wbtickers
df = pd.DataFrame(data=wbdata)
wbpositions = dash_table.DataTable(
    id='wbpositions', 
    columns=wbcolumns,
    data=df.to_dict('records'),
    style_as_list_view=True,
    style_data_conditional=[
        #{
        #    'if' : {'column_id' : 'wbname'},
        #    'textAlign' : 'left'
        #}
        {
            'if' : {
                'filter_query' : '{wbunrealizedprofitloss} > 0',
                'column_id' : 'wbunrealizedprofitloss'
                },
            'backgroundColor' : 'green'
        },
        {
            'if' : {
                'filter_query' : '{wbunrealizedprofitloss} < 0',
                'column_id' : 'wbunrealizedprofitloss'
                },
            'backgroundColor' : 'red'
        },
    ],
    sort_action='native',
    row_selectable='single',
    style_table={'height':'100%'}
)
#############################3

# Stop Loss / Take Profit Alerts
alert_factor = 0.75
sltickers, slprices, slstoplosses, slproximity, slpotentialloss = [], [], [], [], []
for i in range(len(wbaccount['openOrders'])):
    order = wbaccount['openOrders'][i] 
    ticker = order['ticker']['symbol']
    if order['comboType'] == 'STOP_LOSS':
        for j in range(len(wbaccount['positions'])):
            if wbaccount['positions'][j]['ticker']['symbol'] == ticker:
                purchasePrice = float(wbaccount['positions'][j]['costPrice'])
                lastPrice     = float(wbaccount['positions'][j]['lastPrice'])
                limitPrice    = float(order['auxPrice'])
                orderShares   = float(order['totalQuantity'])
                proximity_factor = 1 - abs((lastPrice - limitPrice) / (purchasePrice - limitPrice))
                if proximity_factor <= 1 and proximity_factor >= alert_factor:
                    sltickers.append(order['ticker']['symbol'])
                    slprices.append(lastPrice)
                    slstoplosses.append(limitPrice)
                    slproximity.append(lastPrice - limitPrice)
                    slpotentialloss.append(orderShares * (limitPrice - purchasePrice))
                    break

slcolumns = [
    {'name' : 'Ticker', 'id' : 'slticker'},
    {'name' : 'Price', 'id' : 'slprice'},
    {'name' : 'Stop Loss', 'id' : 'slstoploss'},
    {'name' : 'Proximity ($)', 'id' : 'slproximity'},
    {'name' : 'Potential Loss', 'id' : 'slpotentialloss'}
]
sldata = {
    'slticker' : sltickers,
    'slprice' : slprices,
    'wlstoploss' : slstoplosses,
    'slproximity' : slproximity,
    'slpotentialloss' : slpotentialloss,
}
sldf = pd.DataFrame(data=sldata)
sltable = dash_table.DataTable(
    id='sltable', 
    columns=slcolumns,
    data=sldf.to_dict('records'),
    style_as_list_view=True,
    sort_action='native',
    row_selectable='single',
    style_table={'width' : '90%', 'height':'90%'}
)




app = dash.Dash(__name__)
bg = BullGraph(start_date=start_date, end_date=end_date)
bs = BullScreener(timeframe=100, ticker_list=wb_ticker_list)

# Creating the Ticker input
app.scripts.config.serve_locally = True
app.css.config.serve_locally = True


# Indicator inputs
Days = dcc.Input(id="Days", type="text", placeholder="Days", debounce=True)
WindowSize = dcc.Input(id="WindowSize", type="text", placeholder="Window Size", debounce=True)
Stride = dcc.Input(id="Stride", type="text", placeholder="Stride", debounce=True)
Threshold = dcc.Input(id="Threshold", type="text", placeholder="Threshold", debounce=True)
Screen    = html.Button('Screen', id='Screen-button', n_clicks=0)

columns = [{'name' : 'Stock', 'id' : 'Stock'}, {'name' : 'Sentiment', 'id' : 'Sentiment'}]
bull_table = dash_table.DataTable(id="bull_table", columns=columns)
graph_style = {'display':'inline-block', 'vertical-align' : 'top', 'margin-left' : '3vw', 'margin-top' : '3vw', 'width':'45%', 'height':'40%'}



def home_page():
    return [
        dcc.Graph(id="main_graph", figure=bg.fig, style=graph_style),
        html.Div(
            children=wbpositions,
            style={'display':'inline-block', 'vertical_align':'right', 'margin-left':'3vw', 'margin-right':'3vw', 'margin-top':'3vw', 'width':'45%', 'height':'45%'}
        ),
        html.Div(
            children=[html.H2('Stop Loss Alerts'), sltable],
            style={'display':'inline-block', 'vertical_align':'left', 'margin-left':'3vw', 'margin-right':'3vw', 'margin-top':'3vw', 'width':'42%', 'height':'20%', 'backgroundColor' : 'red'}
        ),
        html.Div(
            children=html.H2('Take Profit Alerts'),
            style={'display':'inline-block', 'vertical_align':'right', 'margin-left':'3vw', 'margin-right':'3vw', 'margin-top':'3vw', 'width':'42%', 'height':'20%', 'backgroundColor' : 'green'}
        )
    ]

app.layout = html.Div(
    children=home_page()
)

@app.callback(Output("main_graph", "figure"), [Input("wbpositions", "selected_rows")])
def display_wb_position(selected_rows):
    for row in selected_rows:
        ticker = wbpositions.data[row]['wbticker']
        bg.ticker = ticker
        fig = bg.createFig()
        fig, historical = bg.styleFig()
        return fig





#@app.callback(Output("bull_table", "data"), 
#[Input("Screen-button", "n_clicks")],
#state=[State(component_id='Days', component_property='value'), 
#State(component_id='WindowSize', component_property='value'), 
#State(component_id='Stride', component_property='value'),
#State(component_id='Threshold', component_property='value')])
#def support_resist_screen(n_clicks, days, windowsize, stride, threshold):
#    sentiments = bs.support_resist_filter(int(days), int(windowsize), int(stride), float(threshold))
##    return sentiments[0:10]


## Rendering the ticker input for the graph
#@app.callback(Output("main_graph", "figure"),
#[Input("WindowSize", "value")])
#def window_size_render(ticker=None):
#    if (ticker == None):
#        bg.ticker = "WindowSize"
#        fig = bg.createFig()
#        fig, historical = bg.styleFig()
#        return fig
#
#    bg.ticker = ticker
#    fig = bg.createFig()
#    fig, historical = bg.styleFig()
#    return fig

if __name__ == "__main__":
    # Initializing stock screener
    #bs.get_trendlines()

    # Run server
    app.run_server(debug=True, use_reloader=False)  # Turn off reloader if inside Jupyter