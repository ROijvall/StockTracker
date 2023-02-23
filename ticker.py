import yfinance as yf
from alarm import Alarm

class Ticker:
    def __init__(self, name, bought = 0, boughtPrice = 0):
        self.name = name.upper()
        self.price = -1
        self.openPrice = -1
        self.bought = bought
        self.boughtPrice = boughtPrice
        self.badTicker = False
        self.referencecount = 1
        self.activealarms = []
        self.triggeredalarms = []
        self.inactivealarms = []
        self.getPrice()
    
    def getPrice(self):
        data = yf.Ticker(self.name)
        print(data)
        today_data = data.history(period='1d')
        if today_data.empty:
            print("Bad ticker")
            self.badTicker = True
            return
        self.openPrice = round((today_data['Open'][0]),2)
        self.price = round((today_data['Close'][0]),2)

    def update(self, price, openPrice, time):
        self.price = price
        self. openPrice = openPrice
        # check alarms
        i = 0
        for alarm in self.activealarms:
            if alarm.checkIfTriggered(price, openPrice, time):
                triggeredAlarm = self.activealarms.pop(i)
                #self.triggeredalarms.append(triggeredAlarm)
                self.inactivealarms.append(triggeredAlarm)
            i += 1

    def get_all_alarms(self):
        return self.activealarms + self.inactivealarms

    def add_alarm(self, alarm):
        if alarm.active:
            self.activealarms.append(alarm)
        else:
            self.inactivealarms.append(alarm)
    
    def remove_alarm(self, index):
        inactiveIndex = index - len(self.activealarms)
        if inactiveIndex >= 0:
            self.inactivealarms.pop(inactiveIndex)
        else:
            self.activealarms.pop(index)

    def increase_ref_count(self):
        self.referencecount += 1

    def decrease_ref_count(self):
        self.referencecount -= 1

    def toJSON(self):
        return self.__dict__  
        
    def __str__(self):
       return self.name