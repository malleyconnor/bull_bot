import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from IPython.display import display, HTML
from dash.dependencies import Input, Output, State
import requests

# TODO: Change to CSS
from BullColors import colors
from BullScreener import BullScreener
from BullGraph import *
import rh_interface

app = dash.Dash(__name__)
bg = BullGraph(start_date=start_date, end_date=end_date)
bs = BullScreener(timeframe=100)
rh_holdings = rh_interface.get_rh_holdings()

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

# Creating dash table of rh holdings
columns = [{'name' : column, 'id' : column} for column in rh_holdings.columns]
holdings_table = dash_table.DataTable(id="holdings_table", columns=columns, data=rh_holdings.to_dict('records'))
graph_style = {'display':'inline-block', 'vertical-align' : 'top', 'margin-left' : '3vw', 'margin-top' : '3vw', 'width':'49%'}


def home_page():
    return [
        dcc.Graph(id="main_graph", figure=bg.fig, style=graph_style),
        html.Div(
            children=holdings_table,
            style={'display':'inline-block', 'vertical_align':'left', 'margin-left':'3vw', 'margin-right':'3vw', 'margin-top':'10vw', 'width':'40%'}
        ),
        html.Div(
            children=bull_table,
            style={'display':'inline-block', 'vertical_align':'right', 'margin-left':'3vw', 'margin-right':'3vw', 'margin-top':'10vw', 'width':'40%'}
        ),
        html.Div(
            children=[
                html.H6("Support / Resist Screener"),
                Days,
                WindowSize,
                Stride,
                Threshold,
                Screen],
            style={'display':'inline-block', 'vertical_align':'right', 'margin-left':'3vw', 'margin-right':'3vw', 'margin-top':'10vw', 'width':'40%'}

        ),
        html.Div(id="ticker_out")

    ]

app.layout = html.Div(
    children=home_page()
)

@app.callback(Output("bull_table", "data"), 
[Input("Screen-button", "n_clicks")],
state=[State(component_id='Days', component_property='value'), 
State(component_id='WindowSize', component_property='value'), 
State(component_id='Stride', component_property='value'),
State(component_id='Threshold', component_property='value')])
def support_resist_screen(n_clicks, days, windowsize, stride, threshold):
    sentiments = bs.support_resist_filter(int(days), int(windowsize), int(stride), float(threshold))
    return sentiments[0:3]


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