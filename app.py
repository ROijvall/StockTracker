#import yfinance as yf
#import tkinter as tk
from watchlist import Watchlist
import time
import os
import PySimpleGUI as sg
import json
import threading
import concurrent.futures
import time

def saveAll(watchlists):
    print("entered saveall")
    result = ""
    for wlist in watchlists:
        tickers = ""
        for ticker in wlist.tickers:
            tickers += json.dumps(ticker.__dict__)
            print(tickers)
        result += wlist.name + ":" + json.dumps(wlist.__dict__) + "\n"
    print(result)
def toolbar(mainMenu):
    if(mainMenu):
        toolbar = [sg.Button("+", key="-ADDWLIST-"), sg.Button("Save", key="-SAVE1-")]
    else:
        toolbar = [sg.Button("<-"), sg.Button("+", key="-ADDTICKER-"), sg.Button("Save", key="-SAVE2-"), sg.Button("🗘")]
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
            print("do we get stuck here?")
            window.write_event_value('-UPDATE-', None)
        else:
            print("No Watchlists found")

def thread_func(wlist):
    wlist.updatePrices()

def main():
    wListNames = []
    wListObjs = []
    try: 
        f = open("watchlists.txt")
        print("found file")

        f.close()
    except IOError:
        print("No saved watchlists found")
    sg.theme('Dark')
    layout1 = [
        [sg.Text("Watchlists")],
        toolbar(True),
        listbox(wListNames, "1")
    ]
    
    layout2 = [
        [sg.Text(size=(20,1),key="-WLIST-")],
        toolbar(False),
        listbox([], "2")
    ]

    layout = [[sg.Column(layout1, key='-COL1-'), sg.Column(layout2, visible=False, key='-COL2-')]]

    window = sg.Window("Stockwatch", layout)
    wListObj = None

    main = [True] #workaround so value gets passed to thread
    signal = threading.Event()
    t = threading.Thread(target=update_watchlists, args=(wListObjs, window, signal))
    t.start()
    while True:
        event, values = window.read()
        if event == "-UPDATE-" and wListObj != None:
            window["-LIST2-"].Update(values = wListObj.tickers)

        if event == "Quit" or event == sg.WIN_CLOSED:
            signal.set()
            break
        if event == "-ADDWLIST-":
            print("addwlist")
            if main[0]:
                event, values = inputPrompt("Add watchlist").read(close=True)
            if event == "Ok":
                wListObjs.append(Watchlist(values[0]))
                print(wListObjs[0].name)
                wListNames.append(values[0])
                window.Element("-LIST1-").Update(values = wListNames)


        if event == "-LIST1-" and wListObjs != []: 
            window[f'-COL1-'].update(visible=False)
            window[f'-COL2-'].update(visible=True)
            
            index = wListNames.index(values["-LIST1-"][0])
            wListObj = wListObjs[index]
            
            window["-WLIST-"].Update(wListObj.name)
            window["-LIST2-"].Update(values = [])
            window["-LIST2-"].Update(values = wListObj.tickers)
            main[0] = False
        if event == "🗘":
            wListObj.updatePrices()
            window["-LIST2-"].Update(values = wListObj.tickers)

        if event == "-ADDTICKER-":
            print("addticker")
            event, values = inputPrompt("Add ticker").read(close=True)
            if event == "Ok":
                wListObj.addTicker(values[0])
                window["-LIST2-"].Update(values = wListObj.tickers)
                print(wListObj.tickers)
        if event == "<-":
            wListObj = None
            window[f'-COL1-'].update(visible=True)
            window[f'-COL2-'].update(visible=False)
            main[0] = True
        if event == "-SAVE1-" or event == "-SAVE2-":
            print("save will crash for now")
            saveAll(wListObjs)

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


