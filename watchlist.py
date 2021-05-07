from ticker import Ticker
import yfinance as yf
import pandas as pd

class Watchlist:

    def __init__(self, name):
        self.name = name
        self.tickers = []

    def addSavedTicker(self, ticker, bought, price):
        self.tickers.append(Ticker(ticker, bought=bought, boughtPrice=price))

    def addTicker(self, ticker, bought=0, price=0):
        data = yf.download(ticker, period="1d", group_by = 'ticker')
        if data.empty:
            print("bad ticker")
        else:
            self.tickers.append(Ticker(ticker, price=round(data['Close'][0], 2), bought=bought, boughtPrice=price))
        
    def deleteTicker(self, window, tickerIndex):
        self.tickers.pop(tickerIndex)
        window.write_event_value('-UPDATE-', None)
        window.write_event_value('-SAVEUPDATE-', None)

    def updatePrices(self):
        stonks = self.tickersToString()
        if stonks.find(" ") != -1:
            data = yf.download(stonks, period="1d", group_by = 'ticker')
            for ticker in self.tickers:
                ticker.updatePrice(round(data[ticker.name]["Close"].values[0], 2))
                if ticker.openPrice == 0:
                    ticker.openPrice = round(data[ticker.name]["Open"].values[0], 2)

        elif stonks != "":
            self.tickers[0].getPrice()

    def tickersToString(self):
        tickerStr = "" 
        for ticker in self.tickers:
            tickerStr += ticker.name + " "
        return tickerStr.rstrip()

    def printTickers(self):
        for ticker in self.tickers:
            print(ticker.name)

    def toJSON(self):
        d = dict()
        for a, v in self.__dict__.items():
            if (hasattr(v, "toJSON")):
                d[a] = v.toJSON()
            else:
                d[a] = v
        return d