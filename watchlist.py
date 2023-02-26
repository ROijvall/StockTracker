from ticker import Ticker
import yfinance as yf
import pandas as pd

class Watchlist:
    def __init__(self, name):
        self.name = name
        self.ticker_names = []

    def get_tickers(self):
        return self.ticker_names

    def add_ticker(self, ticker):
        if ticker in self.ticker_names:
            return
        else:
            self.ticker_names.append(ticker.upper()) 

    def delete_ticker(self, tickerIndex):
        ticker = self.ticker_names.pop(tickerIndex)
        return ticker

    def toJSON(self):
        d = dict()
        for a, v in self.__dict__.items():
            if (hasattr(v, "toJSON")):
                d[a] = v.toJSON()
            else:
                d[a] = v
        return d
    
    def __str__(self):
       return self.name