from ticker import Ticker
import yfinance as yf
import pandas as pd

class Watchlist:

    def __init__(self, name):
        self.name = name
        self.tickers = []
    def addTicker(self, ticker):
        data = yf.download(ticker, period="1d", group_by = 'ticker')
        if data.empty:
            print("bad ticker")
        else:
            self.tickers.append(Ticker(ticker, round(data['Close'][0], 2)))
        
    def updatePrices(self):
        stonks = self.tickersToString()
        if stonks.find(" ") != -1:
            data = yf.download(stonks, period="1d", group_by = 'ticker')
            for ticker in self.tickers:
                ticker.updatePrice(round(data[ticker.name]["Close"].values[0], 2))

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
