# import yfinance as yf
# import tkinter as tk
from PySimpleGUI.PySimpleGUI import EVENT_SYSTEM_TRAY_ICON_ACTIVATED
from watchlist import Watchlist
from alarm import Alarm
from ticker import Ticker
import time
import os
import PySimpleGUI as sg
import json
import threading
import concurrent.futures
import time
import ast
import datetime
import yfinance as yf


def saveAll(tickers, watchlists, file):
    print("entered saveall")
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
    if menu == 0:
        toolbar = [sg.Button("+", key="-ADDWLIST-"),
                   sg.Button("🗑", key="-DELETEWLIST-")]
    elif menu == 1:
        toolbar = [sg.Button("←", key="-LEAVETICKERS-"), sg.Button("+", key="-ADDTICKER-"),
                   sg.Button("🗑", key="-DELETETICKER-"), sg.Button("⏰", key="-ENTERALARM-")]
    elif menu == 2:
        toolbar = [sg.Button("←", key="-LEAVEALARMS-"), sg.Button("+", key="-ADDALARM-"),
                   sg.Button("🗑", key="-DELETEALARM-"), sg.Button("↻", key="-ACTIVATEALARM-")]
    return toolbar


def inputPrompt(prompt):
    layout = [
        [sg.InputText()],
        [sg.Cancel(), sg.Ok()]
    ]
    return sg.Window(prompt, layout, resizable=True)


def tickerPrompt(prompt):
    layout = [
        [sg.InputText()],
        [sg.Text("OPTIONAL - input amount of owned shares")],
        [sg.InputText()],
        [sg.Text("OPTIONAL - input total purchase price of owned shares")],
        [sg.InputText()],
        [sg.Cancel(), sg.Ok()]
    ]
    return sg.Window(prompt, layout, resizable=True)


def alarmPrompt(prompt):
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


def doubleCheckPrompt(prompt):
    layout = [
        [sg.Cancel(), sg.Ok()]
    ]
    return sg.Window(prompt, layout)


def update_all_tickers(tickers, window, signal):
    while not signal.wait(10):
        keys = tickers.keys()
        if len(keys) > 0:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.map(thread_func, tickers, keys)
            window.write_event_value('-UPDATE-', None)
        else:
            print("No tickers found")


def update_watchlists(wListObjs, window, signal):
    while not signal.wait(10):
        if wListObjs != []:
            print("Attempted update")
            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.map(thread_func, wListObjs)
            window.write_event_value('-UPDATE-', None)
        else:
            print("No Watchlists found")


def update_tickers(window, wListObj, tickers):
    result = to_table_data(tickers, wListObj.tickernames)
    window["-TICKERTABLE-"].Update(values=result[0], row_colors=result[1])


def update_alarms(window, ticker, time):
    result = alarm_to_table(ticker, time)
    window["-ALARMTABLE-"].Update(values=result[0], row_colors=result[1])


def alarm_to_table(ticker, time):
	newValues = list()
	colors = list()
	i = 0
	print(ticker.get_all_alarms())
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
		if alarm.expiry != None and alarm.active:
			delta = alarm.expiry - time
			seconds = delta.total_seconds()
			minutes = seconds / 60
			hours = minutes / 60
			print("h: " + str(hours) + " m: " +
					str(minutes) + " s: " + str(seconds))
			if hours > 1:
				values.append(str(int(hours))+"h")
			elif minutes > 1:
				values.append(str(int(minutes))+"m")
			else:
				values.append(str(int(minutes)/60)+"s")
		else:
			values.append("N/A")
		if alarm.active:
			colors.append(tuple([i, "#008000"]))
		else:
			colors.append(tuple([i, "#808080"]))
		newValues.append(values)
		i += 1
	print(newValues)
	return tuple([newValues, colors])


def to_table_data(tickers, data):
    newValues = list()
    colors = list()
    i = 0
    for tickername in data:
        ticker = tickers[tickername]
        values = list()
        values.append(ticker.name)
        values.append(ticker.price)
        if (ticker.openPrice != 0):
            values.append(round(ticker.price - ticker.openPrice, 2))
            values.append(
                str(round((100 * (ticker.price - ticker.openPrice) / ticker.openPrice), 2)) + "%")
            # color logic (postive price movement green, negative red and neutral gray)
            if (ticker.price - ticker.openPrice > 0):
                colors.append(tuple([i, "#008000"]))
            elif (ticker.price - ticker.openPrice < 0):
                colors.append(tuple([i, "#FF0000"]))
            else:
                colors.append(tuple([i, "#808080"]))
        else:
            values.append(0)
            values.append("0%")
            colors.append(tuple([i, "#808080"]))
        if (ticker.bought != 0):
            totValue = ticker.price * ticker.bought
            values.append(str(round(totValue, 2)))
            values.append(str(round((totValue-ticker.boughtPrice), 2)))
            values.append(
                str(round((100 * (totValue - ticker.boughtPrice) / ticker.boughtPrice), 2)) + "%")
        else:
            for _ in range(3):
                values.append("N/A")
        newValues.append(values)
        i += 1
    print(newValues)
    return tuple([newValues, colors])


def thread_func(tickers, keys):
    time = datetime.datetime.now()
    print(keys)
    if keys.find(" ") != -1:
        data = yf.download(keys, period="1d", group_by='ticker')
        for ticker in tickers:
            currentPrice = round(data[ticker.name]["Close"].values[0], 2)
            openPrice = round(data[ticker.name]["Open"].values[0], 2)
            ticker.update(currentPrice, openPrice, time)


def JSONify(Obj):
    if hasattr(Obj, 'toJSON'):
        return Obj.toJSON()
    else:
        raise TypeError


def loadSaved(file):
    lines = file.readlines()
    if lines != "":
        wlists = []
        wlistnames = []
        tickers = {}
        readingTickers = True
        for line in lines:
            if line.startswith("END1"):
                readingTickers = False
                continue
            if readingTickers:
                ticker_dict = json.loads(line)
                ticker = ticker_dict['name']
                print(ticker)
                tickers[ticker] = Ticker(ticker_dict['name'])
                for a in ticker_dict['activealarms']:
                    alarm = Alarm(name=a['name'], over=a['over'], under=a['under'], intraday_percent=a['intraday_percent'], expiry=a['expiry'], active=a['active'])
                    tickers[ticker].add_alarm(alarm)
                for a in ticker_dict['inactivealarms']:
                    alarm = Alarm(name=a['name'], over=a['over'], under=a['under'], intraday_percent=a['intraday_percent'], expiry=a['expiry'], active=a['active'])
                    tickers[ticker].add_alarm(alarm)
            else:
                wlist_dict = json.loads(line)
                wlist = Watchlist(wlist_dict['name'])
                for ticker in wlist_dict['tickernames']:
                    wlist.addTicker(ticker)
                    tickers[ticker].increase_ref_count()
                wlists.append(wlist)
                wlistnames.append(wlist_dict['name'])
        return tickers, wlists, wlistnames
    print("file reading failed")


def main():
    wListNames = []
    wListObjs = []
    tickers = {}
    try:
        with open("saved.txt", 'r+') as f:
            print("found file")
            # load the file if it exists
            tickers, wListObjs, wListNames = loadSaved(f)
            print(wListNames)
            f.close()
    except IOError:
        f = open("saved.txt", 'x')
        # just create the file then close it
        print("No saved watchlists found")

    sg.theme('Dark Blue 3')
    layout1 = [
        [sg.Text("Watchlists")],
        toolbar(0),
        [sg.Listbox(values=wListNames, enable_events=True, size=(
            40, 20), key="-LIST-", bind_return_key=True)]
    ]
    layout2 = [
        [sg.Text(size=(20, 1), key="-WLIST-")],
        toolbar(1),
        [sg.Table(values=[], headings=["Ticker", "Price", "Change", "%", "Value", "P/L", "P/L %"], num_rows=15, def_col_width=7, auto_size_columns=False, key="-TICKERTABLE-", enable_events=True)]
    ]

    layout3 = [
        [sg.Text(size=(20, 1), key="-ALARM-")],
        toolbar(2),
        [sg.Table(values=[], headings=["Stock", "Over", "Under", "Intraday%", "Expiry"], num_rows=15, def_col_width=7, auto_size_columns=False, key="-ALARMTABLE-", enable_events=True)]

    ]

    layout = [[sg.Column(layout1, key='-WLISTS-'), sg.Column(layout2, visible=False,
                         key='-TICKERS-'), sg.Column(layout3, visible=False, key='-ALARMS-')]]

    window = sg.Window("StockTracker", layout).finalize()
    if wListNames != []:
        window.Element("-LIST-").Update(values=wListNames)

    wListObj = None
    signal = threading.Event()
    t = threading.Thread(target=update_all_tickers,
                         args=(tickers, window, signal))
    t.start()
    selectedRow = None
    selectedWlist = ""
    alarmTicker = ""
    while True:
        event, values = window.read()
        if event == "-UPDATE-" and wListObj != None:
            update_tickers(window, wListObj, tickers)
            if alarmTicker != None and alarmTicker in tickers:
                update_alarms(
                    window, tickers[alarmTicker], datetime.datetime.now())

        if event == "-TICKERTABLE-" and values["-TICKERTABLE-"] != []:
            print(values)
            selectedRow = values["-TICKERTABLE-"][0]

        if event == "-ALARMTABLE-" and values["-ALARMTABLE-"] != []:
            print(values)
            selectedRow = values["-ALARMTABLE-"][0]

        if event == "Quit" or event == sg.WIN_CLOSED:
            signal.set()
            break
        if event == "-ADDWLIST-":
            event, values = inputPrompt("Add watchlist").read(close=True)
            if event == "Ok":
                wListObjs.append(Watchlist(values[0]))
                wListNames.append(values[0])
                window.Element("-LIST-").Update(values=wListNames)
                window.write_event_value('-SAVEUPDATE-', None)

        if event == "-LIST-":
            if values["-LIST-"][0] == selectedWlist:  # double click
                window.write_event_value('-ENTERWLIST-', None)
            else:
                selectedWlist = values["-LIST-"][0]

        if event == "-ENTERWLIST-" and selectedWlist != "":
            window[f'-WLISTS-'].update(visible=False)
            window[f'-TICKERS-'].update(visible=True)

            index = wListNames.index(values["-LIST-"][0])
            wListObj = wListObjs[index]

            window["-WLIST-"].Update(wListObj.name)
            update_tickers(window, wListObj, tickers)

        if event == "-ADDTICKER-":
            event, values = tickerPrompt("Add ticker").read(close=True)
            if event == "Ok":
                name = values[0].upper()
                if name in tickers:
                    print("ticker already exists, upping refcount")
                    wListObj.addTicker(name)
                    tickers[name].referencecount += 1
                else:
                    ticker = None
                    if values[1] != "" and values[2] != "":
                        ticker = Ticker(name, float(
                            values[1]), float(values[2]))
                    else:
                        ticker = Ticker(name)
                    if ticker.badTicker:
                        print("bad ticker")
                    else:
                        tickers[name] = ticker
                        wListObj.addTicker(name)
                        tickers[name].referencecount += 1
                        print(wListObj.tickernames)
                        update_tickers(window, wListObj, tickers)
                        window.write_event_value('-SAVEUPDATE-', None)

        if event == "-ENTERALARM-" and selectedRow != None:
            print(wListObj.tickernames[selectedRow])
            alarmTicker = wListObj.tickernames[selectedRow]
            window[f'-WLISTS-'].update(visible=False)
            window[f'-TICKERS-'].update(visible=False)
            window[f'-ALARMS-'].update(visible=True)
            window["-ALARM-"].Update(alarmTicker)
            if alarmTicker not in tickers:
                tickers[alarmTicker] = Ticker(alarmTicker)
            selectedRow = None

        if event == "-ADDALARM-":
            event, values = alarmPrompt(
                "Add alarm for: " + alarmTicker).read(close=True)
            newAlarm = Alarm(alarmTicker)
            if event == "Ok":
                # means one of the three conditions are filled
                if values[0] != "" or values[1] != "" or values[2] != "":
                    newAlarm = Alarm(alarmTicker)
                    if (values[0] != ""):
                        newAlarm.setOver(float(values[0]))
                    if (values[1] != ""):
                        newAlarm.setUnder(float(values[1]))
                    if (values[2] != ""):
                        newAlarm.setIntraday(float(values[2]))
                    if (values[3] != ""):
                        newAlarm.setExpiry(float(values[3]))
                    # .addTicker(values[0], float(values[1]), float(values[2])
                    tickers[alarmTicker].add_alarm(newAlarm)
                else:
                    print("invalid input ")
                update_alarms(
                    window, tickers[alarmTicker], datetime.datetime.now())
                window.write_event_value('-SAVEUPDATE-', None)

        if event == "-LEAVETICKERS-":
            wListObj = None
            selectedRow = None
            window[f'-WLISTS-'].update(visible=True)
            window[f'-TICKERS-'].update(visible=False)
            window[f'-ALARMS-'].update(visible=False)

        if event == "-LEAVEALARMS-":
            selectedRow = None
            alarmTicker = None
            window[f'-WLISTS-'].update(visible=False)
            window[f'-TICKERS-'].update(visible=True)
            window[f'-ALARMS-'].update(visible=False)

        if event == "-DELETEWLIST-" and selectedWlist != "":
            confirm = sg.popup_yes_no(
                "Are you sure you want to delete " + selectedWlist + "?")
            if confirm == "Yes":
                print("entered ok")
                index = wListNames.index(selectedWlist)
                wListNames.pop(index)
                wListObjs.pop(index)
                window.Element("-LIST-").Update(values=wListNames)
                window.write_event_value('-SAVEUPDATE-', None)

        if event == "-DELETETICKER-" and selectedRow != None:
            ticker = wListObj.deleteTicker(selectedRow)
            tickers[ticker].referencecount -= 1
            if tickers[ticker].referencecount == 0:
                tickers.pop(ticker.name)

        if event == "-DELETEALARM-" and selectedRow != None:
            alarmTicker.remove_alarm(selectedRow)
            update_alarms(
                window, tickers[alarmTicker], datetime.datetime.now())

        # if event == "-ACTIVATEALARM-" and selectedRow != None:
        #    numActive = len(tickers[alarmTicker]["active"])
        #    if selectedRow > numActive:
        #        tmp = tickers[alarmTicker]["inactive"].pop(selectedRow-numActive)
        #        tmp.active = True
        #        tickers[alarmTicker]["active"].append(tmp)
        #        update_alarms(window, tickers[alarmTicker]["inactive"], datetime.datetime.now())
        #        update_alarms(window, tickers[alarmTicker]["active"], datetime.datetime.now())
        #    else:
        #        print("Pick an inactive alarm")

        if event == "-SAVEUPDATE-":
            saveAll(tickers, wListObjs, "saved.txt")

    t.join()
    window.close()
    print("Successfully closed the window and thread")
    exit()


main()
