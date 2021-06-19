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
from finvizfinance.screener.technical import Technical






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
positions_style = {'display':'inline-block', 'vertical-align' : 'right', 'width':'100%', 'height' : '50%'}
wbpositions = dash_table.DataTable(
    id='wbpositions', 
    columns=wbcolumns,
    data=df.to_dict('records'),
    style_as_list_view=True,
    style_data_conditional=[
        {
            'if' : { 'row_index' : 'odd'},
            'backgroundColor' : '#776871'
        },
        {
            'if' : { 'row_index' : 'even'},
            'backgroundColor': '#364156'
        },
        {
            'if' : {
                'filter_query' : '{wbunrealizedprofitloss} > 0',
                'column_id' : 'wbunrealizedprofitloss'
                },
            'backgroundColor' : '#85B79D'
        },
        {
            'if' : {
                'filter_query' : '{wbunrealizedprofitloss} < 0',
                'column_id' : 'wbunrealizedprofitloss'
                },
            'backgroundColor' : '#D33F49'
        },
    ],
    sort_action='native',
    row_selectable='single',
    style_table=positions_style,
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
sl_style = {'display':'inline-block', 'float' : 'left', 'vertical-align' : 'left', 'margin-left' : '5%', 'margin-right' : '5%', 'margin-bottom' : '5%', 'width':'90%', 'height' : '75%'}
sltable = dash_table.DataTable(
    id='sltable', 
    columns=slcolumns,
    data=sldf.to_dict('records'),
    style_as_list_view=True,
    sort_action='native',
    row_selectable='single',
    style_table=sl_style
)

#Take Profit Alerts
alert_factor = 0.75
tptickers, tpprices, tplimitprice, tpproximity, tppotentialprofit = [], [], [], [], []
for i in range(len(wbaccount['openOrders'])):
    order = wbaccount['openOrders'][i] 
    ticker = order['ticker']['symbol']
    if order['comboType'] == 'STOP_PROFIT':
        for j in range(len(wbaccount['positions'])):
            if wbaccount['positions'][j]['ticker']['symbol'] == ticker:
                purchasePrice = float(wbaccount['positions'][j]['costPrice'])
                lastPrice     = float(wbaccount['positions'][j]['lastPrice'])
                limitPrice    = float(order['lmtPrice'])
                orderShares   = float(order['totalQuantity'])
                proximity_factor = 1 - abs((lastPrice - limitPrice) / (purchasePrice - limitPrice))
                if proximity_factor <= 1 and proximity_factor >= 0 and proximity_factor >= alert_factor:
                    tptickers.append(order['ticker']['symbol'])
                    tpprices.append(lastPrice)
                    tplimitprice.append(limitPrice)
                    tpproximity.append(lastPrice - limitPrice)
                    tppotentialprofit.append(orderShares * (limitPrice - purchasePrice))
                    break
tpcolumns = [
    {'name' : 'Ticker', 'id' : 'tpticker'},
    {'name' : 'Price', 'id' : 'tpprice'},
    {'name' : 'Limit Price', 'id' : 'tplimitprice'},
    {'name' : 'Proximity ($)', 'id' : 'tpproximity'},
    {'name' : 'Potential Profit', 'id' : 'tppotentialprofit'}
]
tpdata = {
    'tpticker' : tptickers,
    'tpprice' : tpprices,
    'tplimitprice' : tplimitprice,
    'tpproximity' : tpproximity,
    'tppotentialprofit' : tppotentialprofit,
}
tpdf = pd.DataFrame(data=sldata)
tp_style = {'display':'inline-block', 'float' : 'left', 'vertical-align' : 'left', 'margin-top' : '5%', 'margin-left' : '5%', 'margin-right' : '5%', 'margin-bottom' : '5%', 'width':'90%', 'height' : '75%'}
tptable = dash_table.DataTable(
    id='tptable', 
    columns=tpcolumns,
    data=tpdf.to_dict('records'),
    style_as_list_view=True,
    sort_action='native',
    row_selectable='single',
    style_table=tp_style
)




app = dash.Dash(__name__)
bg = BullGraph(start_date=start_date, end_date=end_date)
#bs = BullScreener(timeframe=100, ticker_list=wb_ticker_list)

# Creating the Ticker input
app.scripts.config.serve_locally = True
app.css.config.serve_locally = True


# Indicator inputs
#Days = dcc.Input(id="Days", type="text", placeholder="Days", debounce=True)
#WindowSize = dcc.Input(id="WindowSize", type="text", placeholder="Window Size", debounce=True)
#Stride = dcc.Input(id="Stride", type="text", placeholder="Stride", debounce=True)
#Threshold = dcc.Input(id="Threshold", type="text", placeholder="Threshold", debounce=True)
#Screen    = html.Button('Screen', id='Screen-button', n_clicks=0)

columns = [{'name' : 'Stock', 'id' : 'Stock'}, {'name' : 'Sentiment', 'id' : 'Sentiment'}]
bull_table = dash_table.DataTable(id="bull_table", columns=columns)
graph_style = {'display':'inline-block', 'vertical-align' : 'left', 'width':'100%', 'height' : '50%', 'backgroundColor' : '#364156'}

soundtrack = html.Audio(autoPlay=True, loop=True, id='music', src='http://127.0.0.1:8050/assets/fresh_beat_no_noise.wav', controls=False, style={'margin-left' : '5%'})

divclass = html.Div(className="flexbox", )

functionStyle_small = {'display':'inline-block', 'vertical_align':'left', 'margin-bottom' : '2%', 'height' : '10%', 'width':'90%', 'backgroundColor' : '#364156', 'border-radius':'25px', 'border-style' : 'solid', 'border-color' : 'green', 'overflow-y' : 'hidden'}
functionStyle_big = {'display':'inline-block', 'vertical_align':'left', 'margin-bottom' : '2%', 'height' : '40%', 'width':'90%', 'backgroundColor' : '#364156', 'border-radius':'25px', 'border-top-width' : '30%', 'border-style' : 'solid', 'border-color' : 'green', 'overflow-y' : 'hidden'}


dropdownFunc = html.Div(children=[html.H2('Take Profit Alerts', style={'margin-left' : '2%', 'color' : 'black', 'position' : 'absolute'}), html.Button(style={'height' : '80px', 'width' : '100%', 'color' : 'black', 'background-color' : 'transparent', 'border-color' : 'transparent'}, id='funcButton0', n_clicks=0), tptable], style=functionStyle_small, id='funcDiv0')


def home_page():
    return [
        html.Div(
            children=[html.H1('Bull Bot', style={'margin-left' : '2.22%', 'color' : '#85B79D', 'height' : '100%', 'margin-left' : '5%'})],
            style={'display':'inline-block', 'vertical_align':'left', 'height' : '5%', 'width' : '100%', 'backgroundColor' : '#0F0F0F'}
        ),
        html.Div(
            children=[dcc.Graph(id="main_graph", figure=bg.fig, style=graph_style), wbpositions], 
            style={'float':'left', 'vertical-align':'left', 'margin-left' : '5%', 'margin-right':'5%', 'margin-top':'2%', 'width':'40%', 'height':'800px', 'backgroundColor' : '#364156'}
        ),
        html.Div(
            children=[
                dropdownFunc,
                html.Div(
                    children=[html.H2('Stop Loss Alerts', style={'margin-left' : '5%', 'color' : 'black'}), sltable],
                    style=functionStyle_small
                ),
                html.Div(
                    children=[
                        html.H2('Bottom Channel Screener', style={'margin-left' : '5%', 'color' : 'black'}),
                        html.Div( 
                            children=[
                                html.Div(
                                    children=dcc.Dropdown(id='dropdown_bottomchannel', options=[{'label' : 'Channel Up (Strong)', 'value' : 'channel_up'},{'label' : 'Channel', 'value' : 'channel'}, ], value='channel_up', clearable=False),
                                    style={'float' : 'left', 'width' : '15%', 'margin-left' : '5%', 'margin-right' : '2.22%'}
                                ),
                                dcc.Input(type='number', placeholder='14 Day RSI Threshold', debounce=True, style={'float' : 'left', 'width' : '15%', 'margin-right' : '2.22%'}),
                                html.Div(
                                    children=dcc.Dropdown(id='dropdown_bcvolatility', options=[{'label' : 'No Volatility Filter', 'value'  : 'nf'}, {'label' : 'Week - 5%', 'value' : 'w5'},{'label' : 'Week - 10%', 'value' : 'w10'}, {'label' : 'Month - 5%', 'value' : 'm5'},{'label' : 'Month - 10%', 'value' : 'm10'}], clearable=False, value='nf'),
                                    style={'float' : 'left', 'width' : '15%', 'margin-right' : '2.22%'}
                                ),
                                html.Button('Screen', id='screen_bottomchannel', n_clicks=0, style={'float' : 'left', 'width' : '15%'})
                            ],
                            style={'display':'inline-block', 'vertical_align':'left', 'width' : '100%', 'margin-bottom':'2%'},
                            id='inputs_bottomchannel'
                        ),

                    ],
                    style=functionStyle_small
                ),
            ],
            style={'float':'left', 'height' : '800px', 'width':'40%', 'margin-top' : '2%', 'margin-right' : '5%', 'overflow-y' : 'auto'}
        ),
        soundtrack
    ]

app.layout = html.Div(
    children=home_page(),
    style={'backgroundColor' : '#2D2E2E'},
    id="app"
)

@app.callback(Output("main_graph", "figure"), [Input("wbpositions", "selected_rows")])
def display_wb_position(selected_rows):
    for row in selected_rows:
        ticker = wbpositions.data[row]['wbticker']
        bg.ticker = ticker
        fig = bg.createFig()
        fig, historical = bg.styleFig()
        return fig

@app.callback(Output("funcDiv0", "style"), [Input("funcButton0", "n_clicks")])
def dropdownFunc0(n_clicks):
    if int(n_clicks) % 2 == 0:
        return functionStyle_small
    else:
        return functionStyle_big


#@app.callback(Output("FuncDiv1", "style"), [Input("FuncButton1", "n_clicks")])
#def dropdownFunc0(n_clicks):
#    if int(n_clicks) % 2 == 0:
#        return functionStyle_small
#    else:
#        return functionStyle_big
#
#
#@app.callback(Output("FuncDiv2", "style"), [Input("FuncButton2", "n_clicks")])
#def dropdownFunc0(n_clicks):
#    if int(n_clicks) % 2 == 0:
#        return functionStyle_small
#    else:
#        return functionStyle_big




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
    app.run_server(debug=False, use_reloader=False)  # Turn off reloader if inside Jupyter