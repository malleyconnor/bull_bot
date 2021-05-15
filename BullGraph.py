import pandas
from pandas_datareader import data
from datetime import datetime
import plotly.graph_objects as go
from BullColors import colors
from TimeUtils import *

class BullGraph(object):
    # TODO: Change to use relative dates from current date
    def __init__(self, ticker="NVDA", start_date=start_date, end_date=end_date):
        self.start_date = start_date
        self.end_date   = end_date
        self.ticker     = ticker
        self.createFig()

    def createFig(self): 
        """
            createFig()
            =================
                Description: Creates historical candlestick graph for the input stock ticker.

                Inputs:
                    - ticker (str): string representing a stock ticker (e.g. NVDA, AMD, FCEL, etc...)

                Output:
                    - None

                Return(s):
                    - fig (go.Figure): figure object
        """
        try:
            self.historical = data.DataReader(self.ticker, "yahoo", self.start_date, self.end_date )
        except IOError:
            self.historical = data.DataReader("NVDA", "yahoo", self.start_date, self.end_date )

        self.historical.reset_index(inplace=True, drop=False)

        # Creating graph
        self.fig = go.Figure(
            data=[go.Candlestick(x=self.historical['Date'],
            open=self.historical['Open'],
            high=self.historical['High'],
            low=self.historical['Low'],
            close=self.historical['Close'])])

        return self.fig

    def styleFig(self):
        if not self.fig:
            # Creating graph
            self.fig = go.Figure(
                data=[go.Candlestick(x=historical['Date'],
                open=self.historical['Open'],
                high=self.historical['High'],
                low=self.historical['Low'],
                close=self.historical['Close'])])


        # Styling the graph
        self.fig.layout = dict({
            "title_x" : 0.5,
            "xaxis_title" : "<b>Date</b>",
            "yaxis_title" : "<b>Price</b>",
            "title" : f"<b>%s</b>" % self.ticker,
            "plot_bgcolor" : colors["plot_background"],
            "paper_bgcolor": colors["background"],
            "xaxis1" : dict(
                gridcolor=colors["plot_gridlines"]    
            ),
            "yaxis1" : dict(
                gridcolor=colors["plot_gridlines"]    
            ),
            "font" : dict(
                color=colors["text"],
                size=18
            )
        })


        self.fig.update_xaxes(
            rangebreaks=[dict(bounds=["sat", "mon"])],
            rangeslider_visible=True,
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all")
                ])
            )
        )

        return self.fig, self.historical
