import os
import json
from  binance_interaction import analyze_symbols, get_candlestick_data, query_binance_status, query_account, query_quote_asset_list
from strategy import strategy_one, strategy_two
import logging
import pandas as pd 

# import setting from json 
def get_project_settings(importFilePath):
    if os.path.exists(importFilePath):
        #open the file 
        f = open(importFilePath, "r")
        project_setting = json.load(f)
        f.close()
        return project_setting



if __name__ == '__main__':
    # Set up the logging
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)


    logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(levelname)s: %(message)s', 
                        filename='Binance_log', filemode='a')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s: %(levelname)s: %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    # GET FILE SETUP. 
    # FILE_PATH = 'settings.json'
    # # import settings 
    # project_settings = get_project_settings(FILE_PATH)
    # Get the status 
    # status = query_BINANCE_STATUS()
    status = True
    BINANCE_STATUS = os.environ.get('BINANCE_STATUS')
    BINANCE_STATUS = BINANCE_STATUS == "True"
    print(f"BINANCE_STATUS:{BINANCE_STATUS}")
    print(f"BINANCE_STATUS type: {type(BINANCE_STATUS)}")
    if status:
        logging.info('--------- Verified Satus Binance ready to go  ---------')
        logging.info(pd.Timestamp.now())

        # api_key = project_settings['BinanceKeys']['API_Key']
        # secret_key = project_settings['BinanceKeys']['Secret_Key']
        api_key = os.environ.get('BINANCE_API_KEY')
        secret_key = os.environ.get('BINANCE_SECRET_KEY')

        print(f"BINANCE_STATUS:{api_key}")
        print(f"Api_key_type: {type(api_key)}")
        
        account =  query_account(api_key,secret_key)
        if account['canTrade']:
            logging.info('--------- Binance account verified ---------')
            # logging.info('--------- Start Strategy 1 ---------')
            # strategy_one(timeframe="1h", percentage_rise=0.5, quote_asset="BUSD", project_settings=BINANCE_STATUS, sell_timeframe='30m' , percent_sell_rise=10)
            logging.info('--------- Start Strategy 2 ---------')
            strategy_two(timeframe="1h", percentage_rise=5, quote_asset="BUSD", project_settings=BINANCE_STATUS, sell_timeframe='30m' , percent_sell_rise=2)
            # get previous executed orders' amount. By either coins amount or trading history. 
            
            




