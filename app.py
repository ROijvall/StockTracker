from PySimpleGUI.PySimpleGUI import EVENT_SYSTEM_TRAY_ICON_ACTIVATED
from watchlist import Watchlist
from alarm import Alarm
from ticker import Ticker
import PySimpleGUI as sg
import json
import threading
import concurrent.futures
import time
from datetime import datetime, timedelta
from playsound import playsound

WATCHLIST_VIEW = 0
TICKER_VIEW = 1
ALARM_VIEW = 2
TRIGGERED_ALARM_VIEW = 3
ALERT_SOUND = './ping-82822.mp3'

def save_all(tickers, watchlists, file):
    print("save_all")
    result = ""
    for key in tickers:
        ticker = tickers[key]
        result += json.dumps(ticker, default=JSONify) + "\n"
    result += "END1" + "\n"
    for wlist in watchlists:
        result += json.dumps(wlist, default=JSONify) + "\n"
    with open(file, "w") as f:
        f.write(result)
        f.close()


def toolbar(menu):
    if menu == WATCHLIST_VIEW:
        toolbar = [sg.Button("+", key="-ADDWLIST-"),
                   sg.Button("🗑", key="-DELETEWLIST-"),
                   sg.Button("🔊", key="-TOGGLESOUND-")]
    elif menu == TICKER_VIEW:
        toolbar = [sg.Button("←", key="-LEAVETICKERS-"), sg.Button("+", key="-ADDTICKER-"),
                   sg.Button("🗑", key="-DELETETICKER-"), sg.Button("⏰", key="-ENTERALARM-")]
    elif menu == ALARM_VIEW:
        toolbar = [sg.Button("←", key="-LEAVEALARMS-"), sg.Button("+", key="-ADDALARM-"),
                   sg.Button("🗑", key="-DELETEALARM-"), sg.Button("↻", key="-ACTIVATEALARM-")]
    elif menu == TRIGGERED_ALARM_VIEW:
        toolbar = [sg.Button("🗑", key="-DELETETRIGGERED-"), sg.Button("↻", key="-ACTIVATETRIGGERED-"), sg.Button("✖", key="-EXITTRIGGERED-")]
    return toolbar

def watchlist_prompt(prompt):
    layout = [
        [sg.InputText()],
        [sg.Cancel(), sg.Ok()]
    ]
    return sg.Window(prompt, layout, resizable=True)


def ticker_prompt(prompt):
    layout = [
        [sg.InputText()],
        [sg.Text("OPTIONAL - input amount of owned shares")],
        [sg.InputText()],
        [sg.Text("OPTIONAL - input total purchase price of owned shares")],
        [sg.InputText()],
        [sg.Cancel(), sg.Ok()]
    ]
    return sg.Window(prompt, layout, resizable=True)


def alarm_prompt(prompt):
    layout = [
        [sg.Text("Only need to input one of over/under/intraday")],
        [sg.Text("Over:")],
        [sg.InputText()],
        [sg.Text("Under")],
        [sg.InputText()],
        [sg.Text("Intraday%")],
        [sg.InputText()],
        [sg.Text("OPTIONAL - expiry in x amount of hours")],
        [sg.InputText()],
        [sg.Cancel(), sg.Ok()]
    ]
    return sg.Window(prompt, layout, resizable=True)


def confirmation_prompt(prompt):
    layout = [
        [sg.Text("Are you sure?")],
        [sg.Cancel(), sg.Ok()]
    ]
    return sg.Window(prompt, layout)

def layout(wlist_names):
    sg.theme('Dark Blue 3')
    layout1 = [
        [sg.Text("Watchlists")],
        toolbar(WATCHLIST_VIEW),
        [sg.Listbox(values=wlist_names, enable_events=True, size=(
            40, 20), key="-WLIST-", bind_return_key=True)]
    ]
    layout2 = [
        [sg.Text("Watchlist:"), sg.Text(size=(20, 1), key="-WLISTREF-")],
        toolbar(TICKER_VIEW),
        [sg.Table(values=[], headings=["Ticker", "Price", "Change", "%", "Value", "P/L", "P/L %"], num_rows=15, def_col_width=7, auto_size_columns=False, key="-TICKERTABLE-", enable_events=True)]
    ]

    layout3 = [
        [sg.Text("Alarms for:"), sg.Text(size=(20, 1), key="-ALARM-")],
        toolbar(ALARM_VIEW),
        [sg.Table(values=[], headings=["Stock", "Over", "Under", "Intraday%", "Expiry"], num_rows=15, def_col_width=7, auto_size_columns=False, key="-ALARMTABLE-", enable_events=True)]
    ]

    layout4 = [
        [sg.Text("Triggered alarms")],
        toolbar(TRIGGERED_ALARM_VIEW),
        [sg.Table(values=[], headings=["Ticker", "Price", "Change", "%", "Value", "P/L", "P/L %"], num_rows=15, def_col_width=7, auto_size_columns=False, key="-TALARMTABLE-", justification='right', enable_events=True)]
    ]

    return [[sg.Column(layout1, key='-WLISTS-'), sg.Column(layout2, visible=False,
                         key='-TICKERS-'), sg.Column(layout3, visible=False, key='-ALARMS-'), sg.Column(layout4, visible=False, key='-TALARMS-')]]

def use_view(window, view, triggered_alarm_visible):
    if view == WATCHLIST_VIEW: 
        window[f'-WLISTS-'].update(visible=True)
        window[f'-TICKERS-'].update(visible=False)
        window[f'-ALARMS-'].update(visible=False)
    elif view == TICKER_VIEW:
        window[f'-WLISTS-'].update(visible=False)
        window[f'-TICKERS-'].update(visible=True)
        window[f'-ALARMS-'].update(visible=False)
    elif view == ALARM_VIEW:
        window[f'-WLISTS-'].update(visible=False)
        window[f'-TICKERS-'].update(visible=False)
        window[f'-ALARMS-'].update(visible=True)
    if triggered_alarm_visible: # should make sure the triggered alarm list is always on the right when visible
        window[f'-TALARMS-'].update(visible=triggered_alarm_visible)

def update_all_tickers(tickers, window, signal, triggered_alarms):
    state_change = False
    while not signal.wait(10):
        items = tickers.items()
        if len(items) > 0:
            results = None
            with concurrent.futures.ThreadPoolExecutor() as executor:
                results = executor.map(thread_func, items)
            for result in results:
                if result != None and result not in triggered_alarms:
                    state_change = True
                    triggered_alarms.append(result)
            if state_change:
                state_change = False
                window.write_event_value('-SAVEUPDATE-', None)            
            window.write_event_value('-UPDATE-', None)
        else:
            print("No tickers found")


def update_tickers(window, ticker_list, tickers, key):  
    result = tickers_to_table(tickers, ticker_list)
    window[key].Update(values=result[0], row_colors=result[1])


def update_alarms(window, ticker, time):
    result = alarms_to_table(ticker, time)
    window["-ALARMTABLE-"].Update(values=result[0], row_colors=result[1])

def alarms_to_table(ticker, time):
	new_values = list()
	colors = list()
	i = 0
	for alarm in ticker.get_all_alarms():
		values = list()
		values.append(alarm.name)
		if alarm.over != 0:
			values.append(alarm.over)
		else:
			values.append("N/A")
		if alarm.under != 0:
			values.append(alarm.under)
		else:
			values.append("N/A")
		if alarm.intraday_percent != 0:
			values.append(alarm.intraday_percent)
		else:
			values.append("N/A")
		if alarm.get_expiry() != None and alarm.is_active():
			delta = alarm.get_expiry() - time
			seconds = delta.total_seconds()
			minutes = seconds / 60
			hours = minutes / 60
			if hours > 1:
				values.append(str(int(hours))+"h")
			elif minutes > 1:
				values.append(str(int(minutes))+"m")
			else:
				values.append(str(int(seconds))+"s")
		else:
			values.append("N/A")
		if alarm.active:
			colors.append(tuple([i, "#008000"]))
		else:
			colors.append(tuple([i, "#808080"]))
		new_values.append(values)
		i += 1
	return tuple([new_values, colors])


def tickers_to_table(tickers, data):
    new_values = list()
    colors = list()
    i = 0
    for ticker_name in data:
        ticker = tickers[ticker_name]
        values = list()
        values.append(ticker.name)
        values.append(ticker.price)
        price, open_price = ticker.get_prices()
        bought_price, bought_amount = ticker.get_bought_data()
        if (open_price != 0):
            values.append(round(price - open_price, 2))
            values.append(
                str(round((100 * (price - open_price) / open_price), 2)) + "%")
            # color logic (postive price movement green, negative red and neutral gray)
            if (ticker.price - ticker.open_price > 0):
                colors.append(tuple([i, "#008000"]))
            elif (ticker.price - ticker.open_price < 0):
                colors.append(tuple([i, "#FF0000"]))
            else:
                colors.append(tuple([i, "#808080"]))
        else:
            values.append(0)
            values.append("0%")
            colors.append(tuple([i, "#808080"]))
        if (bought_amount != 0):
            total_value = price * bought_amount
            values.append(str(round(total_value, 2)))
            values.append(str(round((total_value-bought_price), 2)))
            values.append(
                str(round((100 * (total_value - bought_price) / bought_price), 2)) + "%")
        else:
            for _ in range(3):
                values.append("N/A")
        new_values.append(values)
        i += 1
    return tuple([new_values, colors])


def thread_func(ticker_tuple):
    ticker = ticker_tuple[1] # first element is key (ticker name)
    if ticker.update(datetime.now()):
        return ticker.get_name()
    else:
        return None

def JSONify(Obj):
    if hasattr(Obj, 'toJSON'):
        return Obj.toJSON()
    else:
        raise TypeError

def load_saved(file):
    print("loading saved data")
    lines = file.readlines()
    if lines != "":
        wlists = []
        wlist_names = []
        tickers = {}
        reading_tickers = True
        for line in lines:
            if line.startswith("END1"):
                reading_tickers = False
                continue
            if reading_tickers:
                ticker_dict = json.loads(line)
                ticker = list(ticker_dict)[0] # only 1 ticker per line
                tickers[ticker] = Ticker(ticker)
                for a in ticker_dict[ticker]['alarms_active']:
                    if a['expiry']:
                        a['expiry'] = datetime.fromisoformat(a['expiry'])
                    alarm = Alarm(name=a['name'], over=a['over'], under=a['under'], intraday_percent=a['intraday_percent'], expiry=a['expiry'], active=a['active'], hours_active=a['hours_active'])
                    tickers[ticker].add_alarm(alarm)
                for a in ticker_dict[ticker]['alarms_inactive']:
                    if a['hours_active'] > 0:
                         a['expiry'] = datetime.now() + timedelta(hours=int(a['hours_active']))
                    alarm = Alarm(name=a['name'], over=a['over'], under=a['under'], intraday_percent=a['intraday_percent'], expiry=a['expiry'], active=a['active'], hours_active=a['hours_active'])
                    tickers[ticker].add_alarm(alarm)
            else:
                wlist_dict = json.loads(line)
                wlist = Watchlist(wlist_dict['name'])
                for ticker in wlist_dict['ticker_names']:
                    wlist.add_ticker(ticker)
                    tickers[ticker].increase_ref_count()
                wlists.append(wlist)
                wlist_names.append(wlist_dict['name'])
        return tickers, wlists, wlist_names
    print("file reading failed")


def main():
    wlist_names = []
    wlists = []
    tickers = {}
    triggered_alarms = []
    triggered_alarms_showing = False
    popup_active = False
    current_view = WATCHLIST_VIEW
    sound_active = False
    try:
        with open("saved.txt", 'r+') as f:
            print("found file")
            # load the file if it exists
            tickers, wlists, wlist_names = load_saved(f)
            print(wlist_names)
            f.close()
    except IOError:
        f = open("saved.txt", 'x')
        # just create the file then close it
        print("No saved watchlists found")

    window = sg.Window("StockTracker", layout(wlist_names)).finalize()
    if wlist_names != []:
        window.Element("-WLIST-").Update(values=wlist_names)

    wlist = None
    signal = threading.Event()
    t = threading.Thread(target=update_all_tickers,
                         args=(tickers, window, signal, triggered_alarms),
                         daemon=True)
    t.start()
    selected_row = None
    selected_talarm = None
    selected_wlist = ""
    selected_ticker = ""
    while True:
        event, values = window.read()

        if event == "-UPDATE-":
            if wlist != None:
                update_tickers(window, wlist.get_tickers(), tickers, "-TICKERTABLE-")
            if selected_ticker != None and selected_ticker in tickers:
                update_alarms(window, tickers[selected_ticker], datetime.now())
            print(len(triggered_alarms))
            if len(triggered_alarms) > 0:
                if not triggered_alarms_showing:
                    window[f'-TALARMS-'].update(visible=True)
                    triggered_alarms_showing = True
                update_tickers(window, triggered_alarms, tickers, "-TALARMTABLE-")
                if sound_active:
                    playsound(ALERT_SOUND, block=False)

        if event == "-TOGGLESOUND-":
            if sound_active:
                sound_active = False
                sg.popup("Sound turned OFF")
            else:
                sound_active = True
                sg.popup("Sound turned ON") 

        if event == "-WLIST-":
            if values["-WLIST-"][0] == selected_wlist:  # double click
                window.write_event_value('-ENTERWLIST-', None)
            else:
                selected_wlist = values["-WLIST-"][0]

        if event == "-TICKERTABLE-" and values["-TICKERTABLE-"] != []:
            selected_row = values["-TICKERTABLE-"][0]

        if event == "-ALARMTABLE-" and values["-ALARMTABLE-"] != []:
            selected_row = values["-ALARMTABLE-"][0]

        if event == "-TALARMTABLE-" and values["-TALARMTABLE-"] != []:
            selected_talarm = values["-TALARMTABLE-"][0]

        if event == "-ADDWLIST-":
            popup_active = True
            event, values = watchlist_prompt("Add watchlist").read(close=True)
            if event == "Ok":
                wlists.append(Watchlist(values[0]))
                wlist_names.append(values[0])
                window.Element("-WLIST-").Update(values=wlist_names)
                window.write_event_value('-SAVEUPDATE-', None)
                popup_active = False
            elif event == "Cancel":
                popup_active = False

        if event == "-ADDTICKER-":
            popup_active = True
            bad_ticker = False 
            event, values = ticker_prompt("Add ticker").read(close=True)
            if event == "Ok":
                name = values[0].upper()
                ticker = None
                if name in tickers:
                    print("ticker already exists, upping refcount")
                    wlist.add_ticker(name)
                    ticker = tickers[name]
                else:
                    ticker = None
                    if values[1] != "" and values[2] != "":
                        ticker = Ticker(name, float(
                            values[1]), float(values[2]))
                    else:
                        ticker = Ticker(name)
                    if ticker.is_bad():
                        print("Bad ticker")
                        bad_ticker = True
                if not bad_ticker:
                    tickers[name] = ticker
                    ticker.increase_ref_count()
                    wlist.add_ticker(name)
                    update_tickers(window, wlist.get_tickers(), tickers, "-TICKERTABLE-")
                    window.write_event_value('-SAVEUPDATE-', None)
            elif event == "Cancel":
                popup_active = False


        if event == "-ADDALARM-" and len(triggered_alarms) == 0:
            popup_active = True
            event, values = alarm_prompt(
                "Add alarm for: " + selected_ticker).read(close=True)
            new_alarm = Alarm(selected_ticker)
            if event == "Ok":
                if values[0] != "" or values[1] != "" or values[2] != "":
                    new_alarm = Alarm(selected_ticker)
                    if (values[0] != ""):
                        new_alarm.set_over(float(values[0]))
                    if (values[1] != ""):
                        new_alarm.set_under(float(values[1]))
                    if (values[2] != ""):
                        new_alarm.set_intraday(float(values[2]))
                    if (values[3] != ""):
                        new_alarm.set_expiry(float(values[3]))
                    tickers[selected_ticker].add_alarm(new_alarm)
                else:
                    print("invalid input ")
                update_alarms(window, tickers[selected_ticker], datetime.now())
                window.write_event_value('-SAVEUPDATE-', None)
            elif event == "Cancel":
                popup_active = False

        if event == "-ENTERWLIST-" and selected_wlist != "":
            current_view = TICKER_VIEW
            use_view(window, current_view, triggered_alarms_showing)
            index = wlist_names.index(values["-WLIST-"][0])
            wlist = wlists[index]
            selected_wlist = ""

            window["-WLISTREF-"].Update(wlist)
            update_tickers(window, wlist.get_tickers(), tickers, "-TICKERTABLE-")

        if event == "-ENTERALARM-" and selected_row != None:
            current_view = ALARM_VIEW
            selected_ticker = wlist.get_tickers()[selected_row]
            use_view(window, current_view, triggered_alarms_showing)
            window["-ALARM-"].Update(selected_ticker)
            if selected_ticker not in tickers:
                tickers[selected_ticker] = Ticker(selected_ticker)
            update_alarms(window, tickers[selected_ticker], datetime.now())
            selected_row = None

        if event == "-LEAVETICKERS-":
            current_view = WATCHLIST_VIEW
            wlist = None
            selected_row = None
            use_view(window, current_view, triggered_alarms_showing)
            window.Element("-WLIST-").Update(values=wlist_names)

        if event == "-LEAVEALARMS-":
            current_view = TICKER_VIEW
            selected_row = None
            selected_ticker = None
            use_view(window, current_view, triggered_alarms_showing)

        if event == "-DELETEWLIST-" and selected_wlist != "":
            confirm = sg.popup_yes_no(
                "Are you sure you want to delete " + selected_wlist + "?")
            if confirm == "Yes":
                index = wlist_names.index(selected_wlist)
                wlist_names.pop(index)
                wlist_tmp = wlists.pop(index)
                for ticker_name in wlist_tmp.get_tickers():
                    tickers[ticker_name].decrease_ref_count()
                    if tickers[ticker_name].get_ref_count() == 0:
                         tickers.pop(ticker_name)
                window.Element("-WLIST-").Update(values=wlist_names)
                selected_wlist = ""
                window.write_event_value('-SAVEUPDATE-', None)

        if event == "-DELETETICKER-" and selected_row != None:
            ticker_name = wlist.delete_ticker(selected_row)
            tickers[ticker_name].decrease_ref_count()
            if tickers[ticker_name].get_ref_count() == 0:
                tickers.pop(ticker_name)
            window.write_event_value('-UPDATE-', None)
            window.write_event_value('-SAVEUPDATE-', None)

        if event == "-DELETETRIGGERED-" and selected_talarm != None:
            ticker_name = triggered_alarms[selected_talarm]
            tickers[ticker_name].delete_all_inactive()
            triggered_alarms.pop(selected_talarm)
            update_tickers(window, triggered_alarms, tickers, "-TALARMTABLE-")
            if current_view == ALARM_VIEW:
                update_alarms(window, tickers[selected_ticker], datetime.now())
            if len(triggered_alarms) == 0:
                window[f'-TALARMS-'].update(visible=False)
                triggered_alarms_showing = False
            selected_talarm = None
            window.write_event_value('-SAVEUPDATE-', None)

        if event == "-DELETEALARM-" and selected_row != None and len(triggered_alarms) == 0:
            tickers[selected_ticker].remove_alarm(selected_row)
            update_alarms(window, tickers[selected_ticker], datetime.now())
            selected_row = None
            window.write_event_value('-SAVEUPDATE-', None)

        if event == "-ACTIVATEALARM-" and selected_row != None and len(triggered_alarms) == 0:
            tickers[selected_ticker].activate_alarm(selected_row)
            update_alarms(window, tickers[selected_ticker], datetime.now())
            window.write_event_value('-SAVEUPDATE-', None)

        if event == "-ACTIVATETRIGGERED-" and selected_talarm != None:
            ticker_name = triggered_alarms[selected_talarm]
            tickers[ticker_name].retrigger_inactive_alarms()
            triggered_alarms.pop(selected_talarm)
            update_tickers(window, triggered_alarms, tickers, "-TALARMTABLE-")
            if current_view == ALARM_VIEW:
                update_alarms(window, tickers[selected_ticker], datetime.now())
            if len(triggered_alarms) == 0:
                    window[f'-TALARMS-'].update(visible=False)
                    triggered_alarms_showing = False
            selected_talarm = None
            window.write_event_value('-SAVEUPDATE-', None)

        if event == "-EXITTRIGGERED-":
            # triggered_alarms = [] seemed to break something, look into it later
            for i in range(0, len(triggered_alarms)):
                triggered_alarms.pop(i)
            selected_talarm = None
            triggered_alarms_showing = False
            window[f'-TALARMS-'].update(visible=False)

        if event == "-SAVEUPDATE-":
            save_all(tickers, wlists, "saved.txt")

        if (event == "Quit" or event == sg.WIN_CLOSED) and not popup_active:
            signal.set()
            break
        elif popup_active and (event == "Quit" or event == sg.WIN_CLOSED):
             popup_active = False
    #t.join()
    window.close()
    print("Successfully closed the window and thread")
    exit()


main()
