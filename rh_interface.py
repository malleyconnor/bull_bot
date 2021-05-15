import pandas as pd
import robin_stocks as rh
import getpass
import random

# ROBIN HOOD
def get_rh_holdings():
    """
    get_rh_holdings(username)
    ==================
        Description:    Logs into robinhood with the specified username and password, 
                        and grabs data of current positions

        Input(s):
            - username (str): username/email of robinhood account

        Output(s):
            - None

        Return(s):
            - security_list (str): String displaying current positions
    """

    username=str(input("Robin Hood E-mail (hit enter to skip): "))
    holdings_data = {}
    values          = {} 
    shares          = {}
    equities        = {}
    changes         = {}
    percent_changes = {}

    if (username != ""):
        rh.authentication.login(username=username), 
        password=str(getpass.getpass(prompt="Robin Hood Password: "))

        securities = rh.profiles.load_security_profile()
        portfolio  = rh.profiles.load_portfolio_profile()
        holdings   = rh.account.build_holdings()

        # Getting holdings data from RobinHood
        tickers = holdings.keys()
        for ticker in tickers:
            this_stock = holdings[ticker]
            values[ticker]          = this_stock['price']
            shares[ticker]          = this_stock['quantity']
            equities[ticker]        = this_stock['equity']
            percent_changes[ticker] = this_stock['percent_change']
            changes[ticker]         = this_stock['equity_change']

            holdings_data[ticker] = {
                'Ticker'         : ticker,
                'Price'          : this_stock['price'],
                'Shares'         : this_stock['quantity'],
                'Percent Change' : this_stock['percent_change'],
                'Equity'         : this_stock['equity'],
                'Change'         : this_stock['equity_change']
            }

    else:
        random.seed()
        tickers = ['FOO', 'BAR', 'BAZ', 'QUX']
        for ticker in tickers:
            holdings_data[ticker] = {
                'Ticker'         : ticker,
                'Price'          : '{:.2}'.format(random.random()*100),
                'Shares'         : '{:.2}'.format(random.random()*100),
                'Percent Change' : '{:.2}'.format(random.random()*100),
                'Equity'         : '{:.2}'.format(random.random()*100),
                'Change'         : '{:.2}'.format(random.random()*100)
            }


    # Creating holdings data
    rh_holdings = pd.DataFrame.from_dict(
        data=holdings_data,
        orient='index', 
        columns=['Ticker', 'Price', 'Shares', 'Percent Change', 'Equity', 'Change']
    )

    return rh_holdings