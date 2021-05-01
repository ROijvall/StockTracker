import yfinance as yf

class Ticker:
    def __init__(self, name, price = -1):
        self.name = name.upper()
        self.price = price
    def getPrice(self):
        data = yf.Ticker(self.name)
        today_data = data.history(period='1d')
        self.price = round((today_data['Close'][0]),2)
    def updatePrice(self, price):
        self.price = price

    def __str__(self):
        return self.name + ": " + str(self.price)