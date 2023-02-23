from ticker import Ticker
import yfinance as yf
import pandas as pd

class Watchlist:
    def __init__(self, name):
        self.name = name
        self.tickernames = []

    def addTicker(self, ticker):
        if ticker in self.tickernames:
            return
        else:
            self.tickernames.append(ticker.upper()) 

    def deleteTicker(self, window, tickerIndex):
        ticker = self.tickers.pop(tickerIndex)
        window.write_event_value('-UPDATE-', None)
        window.write_event_value('-SAVEUPDATE-', None)
        return ticker.name

    def tickersToString(self):
        tickerStr = "" 
        for ticker in self.tickers:
            tickerStr += ticker.name + " "
        return tickerStr.rstrip()

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