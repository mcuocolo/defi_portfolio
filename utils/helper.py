import pandas as pd
from binance.spot import Spot
from datetime import datetime
import logging
import time
client = Spot()

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)


def token_candles_timed(token, interval, **kwargs):
    """ Return candles/klines of token for given interval
    returns DF as float and datetime index
    **kwargs :
    limit (int, optional): limit the results. Default 500; max 1000.
    startTime (int, optional): Timestamp in ms to get aggregate trades from INCLUSIVE.
    endTime (int, optional): Timestamp in ms to get aggregate trades until INCLUSIVE.
    Naming of columns=["Date", "Open", "High", "Low", "Close", "Volume"] optimized to use with Backtesting.py framework

    """

    data_token = client.klines(token, interval, **kwargs)
    df_token = pd.DataFrame(data_token, columns=["Date", "Open", "High", "Low", "Close", "Volume",
                                                    "close time", "quoted asset", "number of trades", "Base asset vol",
                                                    "Quoted asset vol", "nothing"])
    df_token["Date"] = pd.to_datetime(df_token["Date"], unit="ms")
    df_token.set_index(["Date"], inplace=True)
    df_token = df_token.drop(["close time", "quoted asset", "number of trades", "Base asset vol",
                                "Quoted asset vol", "nothing"], axis=1)
    df_token = df_token.astype(float)
    return df_token

def get_candles(token, interval, startDate, endDate, to_file=False, folder=""):
    """Pass startDate and endDate as string "YYYY-mm-dd"
    All dates are INCLUSIVE
    first candle starts at 00:00 and last candle 00:00 - interval
    Date value = open time for each candle
    Function builds data one day at a time
    tested for 5m, 15m, 1h and 4h
    if to_file=True saves concatenated DF to ../{specified folder}/
    else returns DF """

    interval = interval
    
    # offset for one hour
    offset = 0
    # compute corrections
    if interval == "3m":
        offset = 3 * 60 * 1000
    elif interval == "5m":
        offset = 5 * 60 * 1000
    elif interval == "15m":
        offset = 15 * 60 * 1000
    elif interval == "1h":
        offset = 60 * 60 * 1000
    elif interval == "4h":
        offset = 4 * 60 * 60 * 1000

    # one day time delta, inclusive so 24h - offset
    delta_1day = 24 * 60 * 60 * 1000 - offset

    # calculate the difference in days and +1 to make it inclusive
    start = datetime.strptime(startDate, "%Y-%m-%d")
    end = datetime.strptime(endDate, "%Y-%m-%d")
    number_days = (end - start).days + 1

    # compensate for timezone
    hour = 60 * 60 * 1000
    # compute start and for the loop,
    # with one hour compensation for timezone
    startTime = int(start.timestamp() * 1000 + hour * 2)

    for day in range(number_days):
        endTime = int(startTime + delta_1day)
        params = {"startTime": startTime,
                    "endTime": endTime}

        if day == 0:
            df_token = token_candles_timed(token, interval, **params)
            

        else:
            df_day = token_candles_timed(token, interval, **params)
            df_token = pd.concat([df_token, df_day])
        

        # increment day
        startTime = int(endTime + offset)
        time.sleep(0.2)

    if to_file:
        entries = df_token.shape[0]
        file = f"{folder}/{token}_{interval}_{entries}_{startDate}_{endDate}.csv"
        df_token.to_csv(file)
        logging.info(f"File saved as {file}")
    else:
        return df_token

def load_data(file):
    """
    function to load csv file and return a DF with appropriate format for backtesting.py 
    with columns=["Open", "High", "Low", "Close", "Volume"]
    and datetime index
    Pass path variable to access file
    """
    data_token = pd.read_csv(file)
    df_token = pd.DataFrame(data_token, columns=["Date", "Open", "High", "Low", "Close", "Volume"])
    df_token["Date"] = pd.to_datetime(df_token["Date"])
    df_token.set_index(["Date"], inplace=True)
    df_token = df_token.astype(float)
    return df_token


### TESTING code    

# generating and saving



# # loading
# path_to_file="data/BTCUSDT_1h_27017_2020-01-01_2023-01-31.csv"

# data = load_data(path_to_file)
# print(data.shape)
# print(data.head())
# print(data.dtypes)
# print(data.tail())



