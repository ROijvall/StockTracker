# StockTrackerLite

Simple and lightweight program that uses the yfinance API to pull data on tickers from Yahoo finance. 

To run the program via command-line you need: yfinance, pysimplegui and playsound

While there are many great applications for tracking your portfolio out there, StockTrackerLite offers two things in particular:
* Light performance
* Free unlimited alarm functionality

The obvious downside is of course that data is only fetched every 10 seconds per default, but that can be adjusted. Adjust at your own discretion.

For performance comparison see Chrome resource usage while running a popular watchlist web application:

![image](https://user-images.githubusercontent.com/34237768/221692186-02c6a398-995b-48af-ae02-6342717aec70.png)

StockTrackerLite resource usage (CPU load increases when thread update thread is running)

![image](https://user-images.githubusercontent.com/34237768/221692450-b9bd7faf-f29e-4c2c-9b44-c5334190a98d.png)

Starting view (adding a watchlist):

![image](https://user-images.githubusercontent.com/34237768/221693135-752d1097-c41a-416b-8f5e-bc23c4c44115.png)

Watchlist view:

![image](https://user-images.githubusercontent.com/34237768/221693297-56b801d5-9197-4d18-8761-0fb85292bab3.png)

Alarm view (can add multiple per ticker)

![image](https://user-images.githubusercontent.com/34237768/221693878-c9c39893-6fa4-46c1-8255-1d763019dbdb.png)

Triggered alarm view shows up on the right of existing view:

![image](https://user-images.githubusercontent.com/34237768/221694076-4dcb7b29-b184-44a5-9aa0-82c7b6bc0f9b.png)

When the triggered alarms are handled, either reactivated or deleted then the view dissapears. 
