import yfinance as yf
from alarm import Alarm

class Ticker:
    def __init__(self, name, bought = 0, bought_price = 0):
        self.name = name.upper()
        self.price = -1
        self.open_price = -1
        self.bought_amount = bought
        self.bought_price = bought_price
        self.bad_ticker = False
        self.ref_count = 1
        self.alarms_active = []
        self.alarms_inactive = []
        self.yf_ticker = yf.Ticker(self.name)
        self.update_price()
    
    def update_price(self):
        self.yf_ticker.fast_info
        today_data = self.yf_ticker.history(period='1d')
        if today_data.empty:
            print("Bad ticker")
            self.bad_ticker = True
            return
        self.open_price = round((today_data['Open'][0]),2)
        self.price = round((today_data['Close'][0]),2)

    def update(self, time):
        self.update_price()
        state_change = False
        i = 0
        for alarm in self.alarms_active[:]:
            if alarm.check_if_triggered(self.price, self.open_price, time):
                self.alarms_active.pop(i)
                self.alarms_inactive.append(alarm)
                state_change = True
            else:
                i += 1
        return state_change

    def get_name(self):
        return self.name

    def get_prices(self):
        return self.price, self.open_price

    def get_bought_data(self):
        return self.bought_price, self.bought_amount

    def get_all_alarms(self):
        return self.alarms_active + self.alarms_inactive

    def add_alarm(self, alarm):
        if alarm.is_active():
            self.alarms_active.append(alarm)
        else:
            self.alarms_inactive.append(alarm)
    
    def remove_alarm(self, index):
        inactiveIndex = index - len(self.alarms_active)
        if inactiveIndex >= 0:
            self.alarms_inactive.pop(inactiveIndex)
        else:
            self.alarms_active.pop(index)

    def activate_alarm(self, index):
        inactive_index = index - len(self.alarms_active)
        if inactive_index >= 0:
            alarm = self.alarms_inactive.pop(inactive_index)
            alarm.activate()
            self.add_alarm(alarm)
        else:
            print("Cannot activate active alarm")            

    def retrigger_inactive_alarms(self):
        for _ in self.alarms_inactive[:]:
            alarm = self.alarms_inactive.pop(0)
            alarm.activate()
            self.add_alarm(alarm)

    def delete_all_inactive(self):
        self.alarms_inactive = []

    def get_ref_count(self):
        return self.ref_count

    def increase_ref_count(self):
        self.ref_count += 1

    def decrease_ref_count(self):
        self.ref_count -= 1

    def is_bad(self):
        return self.bad_ticker

    def toJSON(self):
        dict = {}
        dict[self.name] = {"alarms_active": self.alarms_active, "alarms_inactive": self.alarms_inactive}
        return dict
        
    def __str__(self):
       return self.name