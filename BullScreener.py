import numpy as np
import pandas as pd
from datetime import date, datetime
import yfinance as yf
from pandas_datareader import data
from sklearn.preprocessing import MinMaxScaler
from tqdm import tqdm

import pandas_datareader
from TimeUtils import *


# TODO: Remove this
import matplotlib.pyplot as plt


class BullScreener(object):
    """
    BullScreener selects from a list of prospective stock tickers, and screens them for various indicators.
    """
    def __init__(self, sector=None, ticker_list=None, timeframe=5):
        self.nyse   = pd.read_csv('tickers/nyse.csv')

        if (sector):
            self.screen_list = list(self.nyse['Symbol'][~(self.nyse['Symbol'] == '') & self.nyse['industry'] == industry])
        else:
            self.screen_list = list(self.nyse['Symbol'][~(self.nyse['Symbol'] == '')])

        if (ticker_list):
            self.screen_list = ticker_list

        self.original_tickers = self.screen_list
        self.screen_list = self.screen_list[0:250]

        # Gets yahoo finance data for selected stock tickers
        self.historical = {}
        self.financials = {}
        for i in tqdm(range(10)):
            ticker = self.screen_list[i] 
            try:
                self.historical[ticker] = data.DataReader(ticker, "yahoo", start='1/1/2021')
                #self.financials[ticker] = yf.Ticker(ticker)
            except pandas_datareader._utils.RemoteDataError:
                continue
            except KeyError:
                continue
        

    def support_resist_filter(self, ndays, window_size, stride, threshold=0.10):
        sentiments = {}
        for ticker in self.screen_list:
            try:
                stock = self.historical[ticker][(len(self.historical[ticker])-ndays):]['Close']
            except KeyError:
                continue

            stock_xvals = np.arange(len(stock))

            stock_fit = np.polyfit(stock_xvals, stock, 1)
            support, resist = self.__support_resist(stock, window_size, stride)
            if len(support) > 1 and len(resist) > 1 and self.__verify_support_resist(support, resist, ndays):
                current_support = support[0] * (ndays - 1) + support[1]
                current_resist  = resist[0] * (ndays - 1) + resist[1]
                current_price   = stock[len(stock)-1]
                sentiments[ticker] = 1 - 2*(current_price - current_support)/(current_resist - current_support)


        stocks = sentiments.keys()
        sentiments = sentiments.values()
        
        zippedstocks = zip(sentiments, stocks)
        zippedstocks = sorted(zippedstocks, reverse=True)
        stocks = [element for _, element in zippedstocks]
        sentiments = [element for element, _ in zippedstocks]
        zippedstocks = zip(stocks, sentiments)

        out_sentiments = [{'Stock' : st, 'Sentiment' : se} for st, se in zippedstocks]

        return out_sentiments


    def __verify_support_resist(self, support, resist, ndays):
        xvals = np.arange(ndays)
        for i in range(len(xvals)):
            support_val = support[0] * xvals[i] + support[1]
            resist_val  = resist[0] * xvals[i]  + resist[1]
            if support_val > resist_val:
                return False

        if (support[0] > 0 and resist[0] > 0) or (support[0] < 0 and resist[0] < 0):
            return True

        return True



    def __max_pool(self, data, window_size, stride):
        ndays = len(data)

        max_vec = np.zeros(len(data))
        max_xvals = np.zeros(len(data))
        max_iter = 0

        begin_window = 0
        end_window = begin_window + window_size

        while end_window <= ndays:
            max_vec[max_iter] = np.max(data[begin_window:end_window])
            max_xvals[max_iter] = begin_window + np.argmax(data[begin_window:end_window])

            begin_window += stride
            end_window += stride
            max_iter += 1

        max_vec = np.trim_zeros(max_vec, 'b')
        max_xvals = np.trim_zeros(max_xvals, 'b')

        return max_xvals, max_vec

    def __min_pool(self, data, window_size, stride):
        ndays = len(data)

        min_vec = np.zeros(len(data))
        min_xvals = np.zeros(len(data))
        min_iter = 0

        begin_window = 0
        end_window = begin_window + window_size
        
        while end_window <= ndays:
            min_vec[min_iter] = np.min(data[begin_window:end_window])
            min_xvals[min_iter] = begin_window + np.argmin(data[begin_window:end_window])

            begin_window += stride
            end_window += stride
            min_iter += 1

        min_vec   = np.trim_zeros(min_vec, 'b')
        min_xvals = np.trim_zeros(min_xvals, 'b')

        return min_xvals, min_vec

    def __open_window(self, data, window_size, stride):
        ndays = len(data)

        open_vec = np.zeros(len(data))
        open_xvals = np.zeros(len(data))
        open_iter = 0

        begin_window = 0
        end_window = begin_window + window_size
        
        while end_window <= ndays:
            open_vec[open_iter] = data[begin_window]
            open_xvals[open_iter] = begin_window

            begin_window += stride
            end_window += stride
            open_iter += 1


        open_vec   = np.trim_zeros(open_vec)
        open_xvals = np.insert(np.trim_zeros(open_xvals), 0, [0])

        return open_xvals, open_vec



    def __close_window(self, data, window_size, stride):
        ndays = len(data)

        close_vec = np.zeros(len(data))
        close_xvals = np.zeros(len(data))
        close_iter = 0

        begin_window = 0
        end_window = begin_window + window_size
        
        while end_window <= ndays:
            close_vec[close_iter] = data[end_window - 1]
            close_xvals[close_iter] = end_window - 1

            begin_window += stride
            end_window += stride
            close_iter += 1


        close_vec   = np.trim_zeros(close_vec)
        close_xvals = np.insert(np.trim_zeros(close_xvals), 0, [0])

        return close_xvals, close_vec


    def __support_resist(self, data, window_size, stride):
        max_xvals, max_vec = self.__max_pool(data, window_size, stride)
        min_xvals, min_vec = self.__min_pool(data, window_size, stride)
        open_xvals, open_vec = self.__open_window(data, window_size, stride)
        close_xvals, close_vec = self.__close_window(data, window_size, stride)

        support_xvals  = np.zeros(len(max_vec))
        support_points = np.zeros(len(max_vec))
        resist_xvals  = np.zeros(len(max_vec))
        resist_points = np.zeros(len(max_vec))


        for i in range(len(max_vec)):
            # Local max
            if max_vec[i] > open_vec[i] and max_vec[i] > close_vec[i]:
                resist_xvals[i]  = max_xvals[i]
                resist_points[i] = max_vec[i]
        
        for i in range(len(min_vec)):
            if min_vec[i] < open_vec[i] and min_vec[i] < close_vec[i]:
                support_xvals[i]  = min_xvals[i]
                support_points[i] = min_vec[i]

        support_points = np.delete(support_points, np.where(support_xvals == 0))
        support_xvals = np.delete(support_xvals, np.where(support_xvals == 0))
        resist_points  = np.delete(resist_points,  np.where(resist_xvals == 0))
        resist_xvals  = np.delete(resist_xvals,  np.where(resist_xvals == 0))


        # Line of best fit
        if len(support_xvals) > 0 and len(resist_xvals) > 0:
            support = np.polyfit(support_xvals, support_points, 1)
            resist  = np.polyfit(resist_xvals, resist_points, 1)

            return support, resist
        else:
            return [], []
        


    



#
#    def get_trendlines(self):
#        """
#        Converts input price data to hough space, and gets trendline,
#        Lots of code used from https://towardsdatascience.com/algorithmically-drawing-trend-lines-on-a-stock-chart-414ed66d0055
#        TODO: In progress
#        """
#        self.trendlines = {}
#        x = np.linspace(0,1, len(self.historical[self.screen_list[0]]))
#        for ticker in self.screen_list:
#            y = self.rescale_data(list(self.historical[ticker]['Close']))
#            turning_points = self.detect_turning_points(y)
#            plt.plot(x, y)
#            edge_x_inds = np.arange(0,len(y))[turning_points != 0]
#            edges_x = x[turning_points == 1]
#            edges_y = y[turning_points == 1]
#            
#            # rho = x*cos(theta) + y*sin(theta)
#            thetas = np.deg2rad(np.linspace(-90, 90, len(edges_x)))
#            print(thetas)
#            cos_thetas = np.cos(thetas)
#            sin_thetas = np.sin(thetas)
#            rhos = np.vstack([np.add(np.multiply(edges_x[i], cos_thetas), np.multiply(edges_y[i], sin_thetas)) for i in range(len(edges_x))]).T
#
#            hough_space = pd.DataFrame(np.around(rhos, 2), index=thetas)     
#            hough_space.plot(legend=None)
#
#            unique_rhos = np.unique(hough_space)            
#            def accumulator(row):
#                rhos, counts = np.unique(row, return_counts=True)
#                s=pd.Series(0, index=unique_rhos)
#                s[rhos] = counts
#                return s
#
#            print(f"LEN == %d" % (len(y)))
#            accumulated = hough_space.apply(accumulator, axis=1)
#            accumulated_index = np.around(accumulated.index, 4)
#
#            # Displaying heatmap
#            fig = plt.figure(figsize=(8,6))
#            sns.heatmap(accumulated)
#            plt.show()
#
#            time_value_lookup_table = {}
#            y = pd.Series(y)
#            for index, rho in np.ndenumerate(rhos):
#                k     = (thetas[index[0]], rho)
#                time  = y.index[edge_x_inds[index[1]]]
#                value = edges_y[index[1]]
#
#                if k in time_value_lookup_table:
#                    time_value_lookup_table[k].add((time, value))
#                else:
#                    time_value_lookup_table[k]=\
#                        SortedKeyList([(time, value)], key=lambda x: x[0])
#
#            
#            theta_indices, rho_indices =\
#                np.unravel_index(np.argsort(accumulated.values, axis=None), accumulated.shape)
#
#            touches   = []
#            distances = []
#            points    = []
#
#            for i in range(len(theta_indices)):
#                tp = (thetas[theta_indices[i]], unique_rhos[rho_indices[i]])
#                if tp in time_value_lookup_table:
#                    p = time_value_lookup_table[tp]
#                    if len(p) > 1:
#                        touches.append(len(p))
#                        distances.append(p[-1][0] - p[0][0] if len(p) > 1 else 0)
#                        points.append(p)
#
#            ranked_lines = pd.DataFrame(
#                {
#                    "touches" : touches,
#                    "distances" : distances,
#                    "points" : points
#                },
#                index=range(len(points), 0, -1)
#            )
#
#            lines = ranked_lines[ranked_lines["distances"] > timedelta(days=30)]
#            y.plot(figsize=(20,8))
#
#            for i, r in lines.iterrows():
#                x = r["points"][0][0], r["points"][-1][0]
#                y = r["points"][0][1], r["points"][-1][1]
#                plt.plot(x, y)
#
#            plt.show()
#
#            print(ranked_lines[-10:0])
#             
#    
#    def rescale_data(self, arr):
#        """
#        Normalizes data in array between 0 and 1
#
#        Args:
#            arr (list): Array to be scaled. Defaults to [].
#
#        Returns:
#            (list): new scaled array
#        """
#        minval = np.min(arr)
#        maxval = np.max(arr)
#        scaled_arr = np.subtract(arr, minval)
#        scaled_arr = np.divide(scaled_arr, maxval-minval)
#        return scaled_arr
#
#    def detect_turning_points(self, y, period=5):
#        """
#            Returns a list of indices, containing the inflection points of y.
#        """
#        turning_points = np.zeros(len(y))
#        for i in range(math.ceil(period/2), len(turning_points)-math.ceil(period/2)):
#            turning_points[i] = self.turning_point(y[i-math.ceil(period/2) : i+math.ceil(period/2)+1 :])
#
#        return turning_points
#
#    def turning_point(self, sub_arr):
#        """
#        Finds a V or an A turning point in the sub array
#
#        Args:
#            sub_arr (list): Array possibly containing a turning point.
#
#        Returns:
#            (int): +1 for V, -1 for A, or 0 for no turning point.
#        """
#        avg = np.mean(sub_arr)
#
#        # Found a bullish inflection point
#        if sub_arr[0] > avg and sub_arr[-1] > avg:
#            return 1
#        # Found a bearish inflection point
#        elif sub_arr[0] < avg and sub_arr[-1] < avg:
#            return -1
#        # No inflection point
#        else:
#            return 0