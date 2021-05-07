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
        toolbar = [sg.Button("+", key="-ADDWLIST-"), sg.Button("🗑", key="-DELETE1-")]
    else:
        toolbar = [sg.Button("←"), sg.Button("+", key="-ADDTICKER-"), sg.Button("🗑", key="-DELETE2-")]
    return toolbar

def inputPrompt(prompt):
    layout= [
        [sg.InputText()],
        [sg.Cancel(), sg.Ok()]
    ]
    return sg.Window(prompt, layout)

def doubleCheckPrompt(prompt):
    layout= [
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
        [sg.Listbox(values=wListNames, enable_events=True, size=(40, 20), key="-LIST-", bind_return_key=True)]
    ]
    layout2 = [
        [sg.Text(size=(20,1),key="-WLIST-")],
        toolbar(False),
        [sg.Table(values = [], headings=["Ticker", "Price", "Change", "%"], num_rows=15, def_col_width=6, auto_size_columns=False, key="-TABLE-", alternating_row_color="#708090", enable_events=True)]
    ]

    layout = [[sg.Column(layout1, key='-COL1-'), sg.Column(layout2, visible=False, key='-COL2-')]]

    window = sg.Window("StockTracker", layout).finalize()
    if wListNames != []:
        window.Element("-LIST-").Update(values = wListNames)

    wListObj = None
    signal = threading.Event()
    t = threading.Thread(target=update_watchlists, args=(wListObjs, window, signal))
    t.start()
    selectedRow = None
    selectedWlist = ""
    while True:
        event, values = window.read()
        if event == "-UPDATE-" and wListObj != None:
            window["-TABLE-"].Update(values = to_table_data(wListObj.tickers))

        if event == "-TABLE-":
            selectedRow = values["-TABLE-"][0]

        if event == "Quit" or event == sg.WIN_CLOSED:
            signal.set()
            break
        if event == "-ADDWLIST-":
            event, values = inputPrompt("Add watchlist").read(close=True)
            if event == "Ok":
                wListObjs.append(Watchlist(values[0]))
                wListNames.append(values[0])
                window.Element("-LIST-").Update(values = wListNames)
                window.write_event_value('-SAVEUPDATE-', None)

        if event == "-LIST-":
            if values["-LIST-"][0] == selectedWlist: # double click
                window.write_event_value('-ENTERWLIST-', None)
            else:
                selectedWlist = values["-LIST-"][0]

        if event == "-ENTERWLIST-" and selectedWlist != "": 
            window[f'-COL1-'].update(visible=False)
            window[f'-COL2-'].update(visible=True)
            
            index = wListNames.index(values["-LIST-"][0])
            wListObj = wListObjs[index]
            
            window["-WLIST-"].Update(wListObj.name)
            window["-TABLE-"].Update(values = to_table_data(wListObj.tickers))

        if event == "-ADDTICKER-":
            event, values = inputPrompt("Add ticker").read(close=True)
            if event == "Ok":
                wListObj.addTicker(values[0])
                window["-TABLE-"].Update(values = to_table_data(wListObj.tickers))
                window.write_event_value('-SAVEUPDATE-', None)
        
        if event == "←":
            wListObj = None
            window[f'-COL1-'].update(visible=True)
            window[f'-COL2-'].update(visible=False)
            selectedRow = None
        
        if event == "-DELETE1-" and selectedWlist != "":
            confirm = sg.popup_yes_no("Are you sure you want to delete " + selectedWlist + "?")
            if confirm == "Yes":
                print("entered ok")
                index = wListNames.index(selectedWlist)
                wListNames.pop(index)
                wListObjs.pop(index)
                window.Element("-LIST-").Update(values = wListNames)
                window.write_event_value('-SAVEUPDATE-', None)


        if event == "-DELETE2-" and selectedRow != None:
            wListObj.deleteTicker(window, selectedRow)

        if event == "-SAVEUPDATE-":
            saveAll(wListObjs, "saved.txt")

    t.join()
    window.close()
    print("Successfully closed the window and thread")
    exit()

main()


