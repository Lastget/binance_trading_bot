import os
from  binance_interaction import  query_account
from strategy import strategy_two
import logging
import pandas as pd 


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

    # Determine bot status wether is trading or testing net from environment variable. 
    status = True
    BINANCE_STATUS = os.environ.get('BINANCE_STATUS')
    BINANCE_STATUS = BINANCE_STATUS == "True"
    print(f"BINANCE_STATUS:{BINANCE_STATUS}")
    print(f"BINANCE_STATUS type: {type(BINANCE_STATUS)}")
    if status:
        logging.info('--------- Verified Satus Binance ready to go  ---------')
        logging.info(pd.Timestamp.now())

        api_key = os.environ.get('BINANCE_API_KEY')
        secret_key = os.environ.get('BINANCE_SECRET_KEY')
        
        account =  query_account(api_key,secret_key)
        if account['canTrade']:
            logging.info('--------- Binance account verified ---------')
            logging.info('--------- Start Strategy 2 ---------')
            # start trading strategy
            strategy_two(timeframe="1h", percentage_rise=5, quote_asset="BUSD", project_settings=BINANCE_STATUS, sell_timeframe='30m' , percent_sell_rise=2)
            
            
            




