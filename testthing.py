import requests
import time
from datetime import datetime, timedelta
import pandas as pd

# Kraken API endpoint
url = "https://api.kraken.com/0/public/OHLC"

# Parameters
pair = "XXBTZUSD"  # BTC/USD pair
interval = 60      # 60-minute intervals

# Calculate the Unix timestamp for the start of today
today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
since = int(time.mktime(today.timetuple()))

# Make the API request
response = requests.get(url, params={"pair": pair, "interval": interval, "since": since})
data = response.json()

# Extract and print the hourly prices
if data["error"]:
    print("Error:", data["error"])
else:
    ohlc_data = data["result"][pair] #ohlc stands for open, high, low, close
    for entry in ohlc_data:
        timestamp = datetime.utcfromtimestamp(entry[0])
        open_price = entry[1]
        high_price = entry[2]
        low_price = entry[3]
        close_price = entry[4]
        print(f"Time: {timestamp}, Open: {open_price}, High: {high_price}, Low: {low_price}, Close: {close_price}")

needed = []
for entry in ohlc_data:
    timestamp = datetime.utcfromtimestamp(entry[0])
    open_price = entry[1]
    high_price = entry[2]
    low_price = entry[3]
    close_price = entry[4]
    needed.append([timestamp, open_price, high_price, low_price, close_price])


def CreateDF(data):
    # Create a DataFrame from the data
    df = pd.DataFrame(data, columns=["Time", "Open", "High", "Low", "Close"])
    # Convert the timestamp to datetime
    df["Time"] = pd.to_datetime(df["Time"], unit='s')
    df.set_index("Time", inplace=True)
    return df


dateframe = CreateDF(needed)
print(dateframe.head())
print(dateframe.tail())