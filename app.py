#import yfinance as yf
#import tkinter as tk
from PySimpleGUI.PySimpleGUI import EVENT_SYSTEM_TRAY_ICON_ACTIVATED
from watchlist import Watchlist
import time
import os
import PySimpleGUI as sg
import json
import threading
import concurrent.futures
import time
import ast

def saveAll(watchlists, file):
    print("entered saveall")
    result = ""
    for wlist in watchlists:
        result += json.dumps(wlist, default=JSONify) + "\n"
    with open(file, "w") as f:
        f.write(result)
        f.close()
def toolbar(mainMenu):
    if mainMenu:
        toolbar = [sg.Button("+", key="-ADDWLIST-"), sg.Button("Save", key="-SAVE1-"), sg.Button("🗑", key="-DELETE1-")]
    else:
        toolbar = [sg.Button("<-"), sg.Button("+", key="-ADDTICKER-"), sg.Button("Save", key="-SAVE2-"), sg.Button("🗑", key="-DELETE2-")]
    return toolbar

def listbox(content, num):
        identifier = "-LIST" + num + "-"
        listbox = [sg.Listbox(values=content, enable_events=True, size=(40, 20), key=identifier)]
            
        return listbox

def inputPrompt(prompt):
    layout= [
        [sg.InputText()],
        [sg.Cancel(), sg.Ok()]
    ]
    return sg.Window(prompt, layout)

def update_watchlists(wListObjs, window, signal):
    while not signal.wait(10):
        if wListObjs != []:
            print("Attempted update")
            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.map(thread_func, wListObjs)
            window.write_event_value('-UPDATE-', None)
        else:
            print("No Watchlists found")

def to_table_data(data):            
    newValues = list()
    for ticker in data:
        values = list()
        values.append(ticker.name)
        values.append(ticker.price)
        if(ticker.openPrice != 0):
            values.append(round(ticker.price - ticker.openPrice,2))
            values.append(str(round((100 * (ticker.price - ticker.openPrice) / ticker.openPrice),2)) + "%")
        else:
            values.append(0)
            values.append("0%")
        newValues.append(values)
    return newValues

def thread_func(wlist):
    wlist.updatePrices()

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
        for line in lines:
            dict = json.loads(line)
            wlist = Watchlist(dict['name'])
            wlistnames.append(dict['name'])
            tickers = dict['tickers']
            for ticker in tickers:
                wlist.addSavedTicker(ticker)
            wlists.append(wlist)
        return wlists, wlistnames
    print("file reading failed")
def main():
    wListNames = []
    wListObjs = []
    try: 
        with open("saved.txt", 'r+') as f:
            print("found file")
            # do some readign of the file here
            wListObjs, wListNames = loadSaved(f)
            print(wListNames)
            f.close()
    except IOError:
        f = open("saved.txt", 'x')
        # just create the file then close it
        print("No saved watchlists found")
    
    sg.theme('Dark Blue 3')
    layout1 = [
        [sg.Text("Watchlists")],
        toolbar(True),
        listbox(wListNames, "1")
    ]
    layout2 = [
        [sg.Text(size=(20,1),key="-WLIST-")],
        toolbar(False),
        #listbox([], "2")
        [sg.Table(values = [], headings=["Ticker", "Price", "Change", "%"], num_rows=10, def_col_width=6, auto_size_columns=False, key="-TABLE-", alternating_row_color="#708090")]
    ]

    layout = [[sg.Column(layout1, key='-COL1-'), sg.Column(layout2, visible=False, key='-COL2-')]]

    window = sg.Window("StockTracker", layout).finalize()
    if wListNames != []:
        window.Element("-LIST1-").Update(values = wListNames)

    wListObj = None
    signal = threading.Event()
    t = threading.Thread(target=update_watchlists, args=(wListObjs, window, signal))
    t.start()
    
    while True:
        event, values = window.read()
        if event == "-UPDATE-" and wListObj != None:
            window["-TABLE-"].Update(values = to_table_data(wListObj.tickers))

        if event == "Quit" or event == sg.WIN_CLOSED:
            signal.set()
            break
        if event == "-ADDWLIST-":
            event, values = inputPrompt("Add watchlist").read(close=True)
            if event == "Ok":
                wListObjs.append(Watchlist(values[0]))
                wListNames.append(values[0])
                window.Element("-LIST1-").Update(values = wListNames)


        if event == "-LIST1-" and wListObjs != []: 
            window[f'-COL1-'].update(visible=False)
            window[f'-COL2-'].update(visible=True)
            
            index = wListNames.index(values["-LIST1-"][0])
            wListObj = wListObjs[index]
            
            window["-WLIST-"].Update(wListObj.name)
            window["-TABLE-"].Update(values = to_table_data(wListObj.tickers))
            #window["-LIST2-"].Update(values = [])
            #window["-LIST2-"].Update(values = wListObj.tickers)
        """if event == "🗘":
            wListObj.updatePrices()
            window["-LIST2-"].Update(values = wListObj.tickers)"""

        if event == "-ADDTICKER-":
            print("addticker")
            event, values = inputPrompt("Add ticker").read(close=True)
            if event == "Ok":
                wListObj.addTicker(values[0])
                window["-TABLE-"].Update(values = to_table_data(wListObj.tickers))
                print(wListObj.tickers)
        if event == "<-":
            wListObj = None
            window[f'-COL1-'].update(visible=True)
            window[f'-COL2-'].update(visible=False)
        
        if event == "-SAVE1-" or event == "-SAVE2-":
            print("save will crash for now")
            saveAll(wListObjs, "saved.txt")

    t.join()
    window.close()
    print("Successfully closed the window and thread")
    exit()
    """
    try:
        exit()
    except RuntimeError:
        print("Closed properly")
    """
main()


