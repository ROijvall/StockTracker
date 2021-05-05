import yfinance as yf

class Ticker:
    def __init__(self, name, price = -1, openPrice = 0):
        self.name = name.upper()
        self.price = price
        self.openPrice = openPrice
    def getPrice(self):
        data = yf.Ticker(self.name)
        today_data = data.history(period='1d')
        if self.openPrice == 0:
            self.openPrice = round((today_data['Open'][0]),2)
        self.price = round((today_data['Close'][0]),2)
    def updatePrice(self, price):
        self.price = price

    def toJSON(self):
        return self.name
        
    def __str__(self):
       return self.name