import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from IPython.display import display, HTML
from dash.dependencies import Input, Output
import requests

# TODO: Change to CSS
from BullColors import colors
from BullGraph import *
from rh_interface import *

app = dash.Dash(__name__)
bg = BullGraph(start_date=start_date, end_date=end_date)
rh_holdings = get_rh_holdings()


# Creating the Ticker input
app.scripts.config.serve_locally = True
app.css.config.serve_locally = True


# Indicator inputs
Days = dcc.Input(id="Days", type="text", placeholder="Days", debounce=True)
WindowSize = dcc.Input(id="WindowSize", type="text", placeholder="Window Size", debounce=True)
Stride = dcc.Input(id="Stride", type="text", placeholder="Stride", debounce=True)
Threshold = dcc.Input(id="Threshold", type="text", placeholder="Threshold", debounce=True)


# Backtester inputs
DAYS = dcc.Input(id="DAYS", type="text", placeholder="500", debounce=True)
RSI_LENGTH = dcc.Input(id="RSI_LENGTH", type="text", placeholder="14", debounce=True)
RSI_OPEN = dcc.Input(id="RSI_OPEN", type="text", placeholder="40", debounce=True)
RSI_CLOSE = dcc.Input(id="RSI_CLOSE", type="text", placeholder="60", debounce=True)
MAX_PER_STOCK = dcc.Input(id="MAX_PER_STOCK", type="text", placeholder="0.00", debounce=True)



# Creating dash table of rh holdings
columns = [{'name' : column, 'id' : column} for column in rh_holdings.columns]
holdings_table = dash_table.DataTable(id="holdings_table", columns=columns, data=rh_holdings.to_dict('records'))
bear_table = dash_table.DataTable(id="bear_table", columns=1)
graph_style = {'display':'inline-block', 'vertical-align' : 'top', 'margin-left' : '3vw', 'margin-top' : '3vw', 'width':'49%'}
app.layout = html.Div(
    style={
        "background-color" : colors["page_background"]
    },
    children=[
        dcc.Graph(id="main_graph", figure=bg.fig, style=graph_style),
        html.Div(
            children=holdings_table,
            style={'display':'inline-block', 'vertical_align':'right', 'margin-left':'3vw', 'margin-right':'3vw', 'margin-top':'10vw', 'width':'40%'}
        ),
        Days,
        WindowSize,
        Stride,
        Threshold,
        #bull_table,
        bear_table,
        DAYS,
        RSI_LENGTH,
        RSI_OPEN,
        RSI_CLOSE,
        MAX_PER_STOCK,
        html.Div(id="ticker_out")
    ]
)

## Rendering the ticker input for the graph
#@app.callback(Output("main_graph", "figure"),
#[Input("ticker_in", "value")])
#def ticker_render(ticker=None):
#    if (ticker == None):
#        bg.ticker = "NVDA"
#        fig = bg.createFig()
#        fig, historical = bg.styleFig()
#        return fig
#
#    bg.ticker = ticker
#    fig = bg.createFig()
#    fig, historical = bg.styleFig()
#    return fig
#
#
# Rendering the ticker input for the graph
@app.callback(Output("main_graph", "figure"),
[Input("WindowSize", "value")])
def window_size_render(ticker=None):
    if (ticker == None):
        bg.ticker = "Window Size"
        fig = bg.createFig()
        fig, historical = bg.styleFig()
        return fig

    bg.ticker = ticker
    fig = bg.createFig()
    fig, historical = bg.styleFig()
    return fig