import datetime

class Alarm:
    def __init__(self, name, over = 0, under = 0, intraday_percent = 0, expiry = None, active = True):
        self.name = name.upper()
        self.over = over
        self.under = under
        self.intraday_percent = intraday_percent
        self.expiry = expiry
        self.active = active

    def checkIfTriggered(self, curr_price, open_price, present_time):
        if curr_price > self.over:
            self.deactivateAlarm()
            return True
        if curr_price < self.under:
            self.deactivateAlarm()
            return True
        if self.isExpired(present_time):
            self.deactivateAlarm()
            return True
        if curr_price <= 0.95 * open_price or curr_price >= 1.05 * open_price: 
            self.deactivateAlarm()
            return True
        return False

    def setOver(self, value):
        self.over = value
    
    def setUnder(self, value):
        self.under = value

    def setIntraday(self, value):
        self.intraday_percent = value
    
    def setExpiry(self, value):
        now = datetime.datetime.now()
        time_change = datetime.timedelta(hours=value)
        self.expiry = now + time_change
        
    def activateAlarm(self):
        self.active = True

    def deactivateAlarm(self):
        self.active = False

    def isExpired(self, present_time):
        if present_time > self.expiry:
            self.deactivateAlarm()
            return True
        return False

    def toJSON(self):
        return self.__dict__  
        
    def __str__(self):
       return self.name