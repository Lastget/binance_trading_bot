from binance.spot import Spot 
import pandas
from strategy import determine_buy_event
import time 
from binance.error import ClientError, ServerError
import logging
import os 

# query Binance and retrieve status 
def query_binance_status():
    status = Spot().system_status()
    if status['status'] == 0: 
        return True 
    else:
        raise ConnectionError


# connect to binance account
def query_account(api_key, secret_key): 
    return Spot(api_key, secret_key).account()

# get BTC/USD price
def get_candlestick_data(symbol, timeframe, qty):
    #  qty : Number of Candles. Querying the right number of previous candles
    raw_data = Spot().klines(symbol=symbol, interval=timeframe, limit=qty)
    # Set up the return array
    converted_data = []
    # Convert each element into a python dictionary object, then add to converted data
    for candle in raw_data:
        converted_candle = {
            'time': candle[0],
            'open': float(candle[1]),
            'high': float(candle[2]),
            'low': float(candle[3]),
            'close': float(candle[4]),
            'volume': float(candle[5]),
            'close_time': candle[6],
            'quote_asset_volume': float(candle[7]),
            'number_of_trades': int(candle[8]),
            'taker_buy_base_asset_volume': float(candle[9]),
            'taker_buy_quote_asset_volume': float(candle[10])
        }
        converted_data.append(converted_candle)

    return converted_data

# form a BUSD Symbol list
def query_quote_asset_list(quote_asset_symbol):
    # Retrieve a list of symbols from Binance. Returns as a dictionary
    symbol_dictionary = Spot().exchange_info() 

    # Convert into a dataframe
    symbol_dataframe = pandas.DataFrame(symbol_dictionary['symbols'])
    
    # Extract only those symbols with a base asset of BUSD and status of TRADING
    quote_symbol_dataframe = symbol_dataframe.loc[symbol_dataframe['quoteAsset'] == quote_asset_symbol]
    quote_symbol_dataframe = quote_symbol_dataframe.loc[quote_symbol_dataframe['status'] == "TRADING"]

    # Return quote_symbol_dataframe 
    return quote_symbol_dataframe  


# Function to extract symbol list into an array ,
def analyze_symbols(symbol_dataframe, timeframe, percentage_rise):
    trading_symbols = []

    for ind in symbol_dataframe.index:
        # Analyze Symbol 
        logging.info(f"Analyze to buy {symbol_dataframe['symbol'][ind]} ...")
        analysis = determine_buy_event(symbol_dataframe['symbol'][ind], timeframe,
                                       percentage_rise)
        
        if analysis:
            trading_symbols.append(symbol_dataframe['symbol'][ind])
        
        # Sleep for one second 
        time.sleep(0.5)
    return trading_symbols 



    


# Make trade if params provided
def make_trade_with_params(params, project_settings):
    if project_settings == True: 
        logging.info("Real Trade")
        # Set API key 
        # api_key = project_settings['BinanceKeys']['API_Key'] 
        # secret_key = project_settings['BinanceKeys']['Secret_Key']
        api_key = os.environ.get('BINANCE_API_KEY')
        secret_key = os.environ.get('BINANCE_SECRET_KEY')
        # Set up client 
        client = Spot(api_key, secret_key)
        
    else: 
        logging.info("Testing Trade")
        # Set API key 
        api_key = os.environ.get('BINANCE_TEST_API_KEY')
        secret_key = os.environ.get('BINANCE_TEST_SECRET_KEY')
        # Set up client 
        client = Spot(api_key, secret_key, base_url= "https://testnet.binance.vision")

    # MAKE the trade 
    try:
        response = client.new_order(**params)
        return response 
    except ConnectionRefusedError as error: 
        logging.error(f"Found error. {error}")
    except ClientError as e: 
        logging.error(f"Client_Error: {e}")
    except ServerError as e: 
        logging.error(f"ServerError: {e}")
     
   
        

# Query open trade 
# Open orders are those unfilled and working orders still in the market waiting to be executed.
def query_open_trades(project_settings):
    # Real trading data 
    if project_settings == True:
        # Set API key 
        api_key = os.environ.get('BINANCE_API_KEY')
        secret_key = os.environ.get('BINANCE_SECRET_KEY')
        # Set up client 
        client = Spot(api_key, secret_key)
    else:
        # Set API key 
        api_key = os.environ.get('BINANCE_TEST_API_KEY')
        secret_key = os.environ.get('BINANCE_TEST_SECRET_KEY')
        # Set up client 
        client = Spot(api_key, secret_key, base_url= "https://testnet.binance.vision")

    try:
        reponse = client.get_open_orders()
        return reponse 
    except ConnectionRefusedError as error: 
        logging.error(f"Found error {error}")
    except ClientError as e: 
        logging.error(f"Client_Error: {e}")
    except ServerError as e: 
        logging.error(f"ServerError: {e}")

# Cancel Order 
def cancel_order_by_symbol(symbol, project_settings):
    if project_settings == True:
        # Set API key 
        api_key = os.environ.get('BINANCE_API_KEY')
        secret_key = os.environ.get('BINANCE_SECRET_KEY')
        # Set up client 
        client = Spot(api_key, secret_key)
    else:
        # Set API key 
        api_key = os.environ.get('BINANCE_TEST_API_KEY')
        secret_key = os.environ.get('BINANCE_TEST_SECRET_KEY')
        # Set up client 
        client = Spot(api_key, secret_key, base_url= "https://testnet.binance.vision")

    try:
        response = client.cancel_open_orders(symbol)
        return response 
    except ConnectionRefusedError as error: 
        logging.error(f"Found error {error}")
    except ClientError as e: 
        logging.error(f"Client_Error: {e}")
    except ServerError as e: 
        logging.error(f"ServerError: {e}")

# Check order
def check_order_by_symbol_id(symbol, order_id, project_settings):
    if project_settings == True:
        # Set API key 
        api_key = os.environ.get('BINANCE_API_KEY')
        secret_key = os.environ.get('BINANCE_SECRET_KEY')
        # Set up client 
        client = Spot(api_key, secret_key)
    else:
        # Set API key 
        api_key = os.environ.get('BINANCE_TEST_API_KEY')
        secret_key = os.environ.get('BINANCE_TEST_SECRET_KEY')
        # Set up client 
        client = Spot(api_key, secret_key, base_url= "https://testnet.binance.vision")

    try:
        response = client.get_order(symbol, orderId = order_id)
        return response 
    except ConnectionRefusedError as error: 
        logging.error(f"Found error {error}")
    except ClientError as e: 
        logging.error(f"Client_Error: {e}")
    except ServerError as e: 
        logging.error(f"ServerError: {e}")


def get_ticker_lot_size(symbol, project_settings):
    if project_settings == True:
        # Set API key 
        api_key = os.environ.get('BINANCE_API_KEY')
        secret_key = os.environ.get('BINANCE_SECRET_KEY')
        # Set up client 
        client = Spot(api_key, secret_key)
    else:
        # Set API key 
        api_key = os.environ.get('BINANCE_TEST_API_KEY')
        secret_key = os.environ.get('BINANCE_TEST_SECRET_KEY')
        # Set up client 
        client = Spot(api_key, secret_key, base_url= "https://testnet.binance.vision")


    try: 
        ex_info = client.exchange_info() 
        infos = ex_info["symbols"]
        for info in infos: 
            if info['symbol'] == symbol: 
                for filter in info['filters']: 
                    if filter['filterType'] == 'PRICE_FILTER':
                        tickSize =  filter['tickSize']
                    if filter['filterType'] == 'LOT_SIZE':
                        lotSize = filter['stepSize']
                return tickSize, lotSize

    except ConnectionRefusedError as error: 
        logging.error(f"Found error {error}")
    except ClientError as e: 
        logging.error(f"Client_Error: {e}")
    except ServerError as e: 
        logging.error(f"ServerError: {e}")




                

