import datetime
import copy

class Alarm:
    def __init__(self, name, over = 0, under = 0, intraday_percent = 0, expiry = None, hours_active = 0, active = True):
        self.name = name.upper()
        self.over = over
        self.under = under
        self.intraday_percent = intraday_percent
        self.expiry = expiry
        self.hours_active = hours_active
        self.active = active

    def check_if_triggered(self, curr_price, open_price, present_time):
        if self.over != 0 and curr_price > self.over:
            self.deactivate()
            print("price is over, deactivate")
            return True
        if self.under != 0 and curr_price < self.under:
            self.deactivate()
            print("price is under, deactivate")
            return True
        if self.is_expired(present_time):
            print("alarm expired, deactivate")
            self.deactivate()
            return True
        if self.intraday_percent != 0: 
            fraction = self.intraday_percent / 100
            delta = abs(1-(curr_price/open_price))
            if delta > fraction:
                print("intraday_percent condition, deactivate")
                self.deactivate()
                return True
        return False

    def set_over(self, value):
        self.over = value
    
    def set_under(self, value):
        self.under = value

    def set_intraday(self, value):
        self.intraday_percent = value
    
    def set_expiry(self, hours):
        self.hours_active = hours
        self.expiry = datetime.datetime.now() + datetime.timedelta(hours=hours)

    def get_expiry(self):
        return self.expiry

    def activate(self):
        if self.hours_active != 0:
            self.set_expiry(self.hours_active)
        self.active = True

    def deactivate(self):
        self.expiry = None
        self.active = False

    def is_active(self):
        return self.active

    def is_expired(self, present_time):
        if self.expiry != None and present_time > self.expiry:
            self.deactivate()
            return True
        return False

    def toJSON(self):
        to_dict = vars(copy.deepcopy(self)) # deep copy to not overwrite anything in the alarm object
        if (self.expiry != None):
            to_dict['expiry'] = self.expiry.isoformat() 
        return to_dict  
        
    def __str__(self):
       return self.name