import pandas 
import numpy 
import binance_interaction
import time 
import math 
import logging 

def get_and_transform_binance_data(symbol, timeframe, number_of_candles):
    # retrieve raw data from binance 
    raw_data = binance_interaction.get_candlestick_data(symbol, timeframe, number_of_candles)

    # transform raw data into Pandas DataFrame 
    df_data = pandas.DataFrame(raw_data)
    
    # Convert time 
    df_data['time'] = pandas.to_datetime(df_data['time'], unit='ms')

    #Convert closetime 
    df_data['close_time'] = pandas.to_datetime(df_data['close_time'], unit='ms')

    # Calculate if Red (trending down) or Green (trending up)
    df_data['RedOrGreen'] = numpy.where((df_data['open'] < df_data['close']), 'Green', 'Red')

    return df_data 

# Function to calculate the percentage price rise as a float
def determine_percent_rise(close_previous, close_current):
    return (close_current-close_previous)/close_previous *100

# Determine "PUMP"
def determine_buy_event(symbol, timeframe, percentage_rise): 
    # retrieve the pevious 3 candles 
    candlestick_data = get_and_transform_binance_data(symbol, timeframe, number_of_candles=3)
    # Determine if last 3 candles are green 
    # if candlestick_data.loc[0,'RedOrGreen'] == "Green" :
    if candlestick_data.loc[0,'RedOrGreen'] == "Green" and candlestick_data.loc[1, 'RedOrGreen']== "Green" and candlestick_data.loc[2, 'RedOrGreen'] == "Green":
        # Determine price rise percentage 
        rise_one = determine_percent_rise(candlestick_data.loc[0,'open'], candlestick_data.loc[0,'close'])
        rise_two = determine_percent_rise(candlestick_data.loc[1,'open'], candlestick_data.loc[1,'close'])
        rise_three = determine_percent_rise(candlestick_data.loc[2,'open'], candlestick_data.loc[2,'close'])
        logging.info(f"rising rate for {symbol}: {rise_one}, and threshole { percentage_rise}")
        if rise_one >= percentage_rise and rise_two >= percentage_rise and rise_three >= percentage_rise:
        # if rise_one >= percentage_rise:
            # We can enter a trade!
            
            return True 
        else:
            return False 
    else:
        return False 

# "SELL" rRises of less than 5% per 30 minutes for two consecutive time periods
def determine_sell_event(symbol, timeframe, percentage_rise): 
    # retrieve the pevious 2 candles 
    candlestick_data = get_and_transform_binance_data(symbol, timeframe, number_of_candles=2)

    # Determine price rise percentage 
    rise_one = determine_percent_rise(candlestick_data.loc[0,'open'], candlestick_data.loc[0,'close'])
    rise_two = determine_percent_rise(candlestick_data.loc[1,'open'], candlestick_data.loc[1,'close'])

    if rise_one <= percentage_rise and rise_two <= percentage_rise:
        # We can SELL a trade!
        return True 
    else:
        return False 

# Calculate SELL parameters,  asset_list which has previous bought BUSD in it.
def calculate_sell_parameters(symbol, timeframe, asset_list, boughtQty, project_setting):
    # see last candle, qty =1  
    raw_data = binance_interaction.get_candlestick_data(symbol, timeframe, qty=1)
    
    tickSize, lotSize = binance_interaction.get_ticker_lot_size(symbol, project_setting)
    tickSize = float(tickSize)
    lotSize  = float(lotSize)

    # Determine the precision required on for the symbol 
    precision = asset_list.loc[asset_list['symbol'] == symbol]
    precision = precision.iloc[0]['baseAssetPrecision']

    # Extract the close price 
    close_price = raw_data[0]["close"]

    # Calculate the buy stop: you assume that the price will go up after this price.  
    stop_price = (close_price * 1.02)
    stop_price  = stop_price //tickSize * tickSize
    stop_price  = math.floor(stop_price  * 10**precision) / 10**precision


    limit_sell_price = stop_price * 0.98
    limit_sell_price  = limit_sell_price //tickSize * tickSize
    limit_sell_price  = math.floor(limit_sell_price  * 10**precision) / 10**precision

    #Calculate the quantity. this will be from previous bought amount 
    quantity = boughtQty

    # Create Parameters dict based on assumption 
    # GTC: Good Til Canceled 
    params = {
       "symbol": symbol,
       "side": 'SELL',
       "type": "TAKE_PROFIT_LIMIT",
       "timeInForce": "GTC", 
       "quantity": quantity, 
       "stopPrice": stop_price, 
       "price": limit_sell_price,
       "trailingDelta": 100  # 1% 
    }   
    
    return params 



# Function to calculate trade parameters, asset_list which has BUSD in it.  
def calculate_trade_parameters(symbol, timeframe, asset_list, project_setting):
    # get filter 
    tickSize, lotSize = binance_interaction.get_ticker_lot_size(symbol, project_setting)
    tickSize = float(tickSize)
    lotSize  = float(lotSize)
    
    # see last candle, qty =1  
    raw_data = binance_interaction.get_candlestick_data(symbol, timeframe, qty=1)
    
    # Determine the precision required on for the symbol 
    precision = asset_list.loc[asset_list['symbol'] == symbol]
    precision = precision.iloc[0]['baseAssetPrecision']

    # Extract the close price 
    close_price = raw_data[0]["close"]

    # Calculate the buy stop: you assume that the price will go up after this price.  
    buy_stop = (close_price * 1.01)
    buy_stop = buy_stop//tickSize * tickSize
    buy_stop  = math.floor(buy_stop  * 10**precision) / 10**precision

    #Calculate the quantity. this will be buy_stop / $100 
    try:
        raw_quantity = 100/buy_stop 
    
        
        # Floor  
        raw_quantity = raw_quantity//lotSize * lotSize 
        quantity = math.floor(raw_quantity * 10**precision) / 10**precision
        logging.info(f"quantity{quantity}")
        logging.info(f"lotSize{lotSize}")
        # Create Parameters dict based on assumption 
        # GTC: Good Til Canceled 
        params = {
        "symbol": symbol,
        "side": 'BUY',
        "type": 'MARKET',
        #    "type": "STOP_LOSS_LIMIT",
        #    "timeInForce": "GTC", 
        "quantity": quantity, 
        #    "price": str(buy_stop),
        #    "trailingDelta": 100  
        }
        logging.info(params)

        return params 

    except:
        logging.info("Error") 
        

# strategy
def strategy_one(timeframe, percentage_rise, quote_asset, project_settings, sell_timeframe, percent_sell_rise): 
    trading_symbols = [] 
    trading_infos =[]
    previous_time = 0 
    prev_sell_time = 0 
    while 1: 
        test_time = get_and_transform_binance_data(symbol ="BTCBUSD", timeframe=timeframe, number_of_candles=1)
        current_time = test_time.iloc[0]['time']
        if current_time != previous_time: 
            logging.info("A new candle!")
            previous_time = current_time 


            logging.info("STEP1. Cancelling open orders")
            # Get a list of open trades 
            open_trades = binance_interaction.query_open_trades(project_settings=project_settings)
            # iterate thorough list 
            for trades in open_trades: 
                executed_qty = float(trades['executedQty'])
                if executed_qty == 0:
                    # Not filled orders cancel 
                    binance_interaction.cancel_order_by_symbol(trades['symbol'], project_settings)
                    logging.info("Order Canceled")
                    trading_symbols.remove(trades['symbol'])
                    # removing order info: orderID & symbol
                    for i in range(len(trading_infos)): 
                        if trading_infos[i]['symbol']==trades['symbol']: 
                            del trading_infos[i]

            
            # Step 2. find new assets to purchase 
            logging.info("STEP2. Analyzing New Assets to purchase")
            asset_list = binance_interaction.query_quote_asset_list(quote_asset_symbol=quote_asset)
            # wether buy or not. buy trading strategy 3 conseccutive growth. 
            new_trading_symbols = binance_interaction.analyze_symbols(asset_list, timeframe, percentage_rise)
            
            # see if symbols are already traded 
            for symbol in new_trading_symbols:
                if symbol not in trading_symbols:
                    # If symbol not already being traed, calculated the trading parameters 
                    logging.info(f"Opening trade on new symbol: {symbol}")
                    trade_parameters = calculate_trade_parameters(symbol, timeframe, asset_list=asset_list, project_setting=project_settings)

                    # make a trade
                    try: 
                        trade_outcome = binance_interaction.make_trade_with_params(trade_parameters, project_settings)
                        logging.info(trade_outcome)
                        # trading success placed added to trading_symbols 
                        trading_symbols.append(symbol)
                        trading_infos.append({"orderId": trade_outcome["orderId"], "symbol": symbol } )
                    
                    except:
                        trade_outcome = False 
                        logging.info("Error placing order")
                        logging.info(f"Error:{trade_outcome}")

            logging.info("Analysis Completed") 

        # Analysis SELLING condition 2 , Sell markets when 2 executive growth rate < 5%
         
        test_time = get_and_transform_binance_data(symbol ="BTCBUSD", timeframe=sell_timeframe, number_of_candles=1)
        sell_current_time = test_time.iloc[0]['time']
        if sell_current_time != prev_sell_time: 
            logging.info("A new half hour candle!")
            logging.info("STEP3. Start Analysis Selling condition") 
            prev_sell_time = sell_current_time

            if trading_infos: 
                # Identify all preivous traded symbols ordered are filled "trading symobls"
                for trade_info in trading_infos:
                    order_id = trade_info['orderId']
                    order_symbol = trade_info['symbol']
                    # Check if symbol pass rate is lower than 5% 
                    logging.info(f"analyze to sell {order_symbol} ...")
                    analysis_sell = determine_sell_event(order_symbol, timeframe = sell_timeframe, percentage_rise = percent_sell_rise) 
                    logging.info(f"analysis_sell: {analysis_sell}")
                    if analysis_sell: 
                        # Check if order is filled 
                        response = binance_interaction.check_order_by_symbol_id(order_symbol, order_id, project_settings=project_settings)
                        logging.info(response)
                        if response['status'] == "FILLED":
                            boughtQty = response['executedQty'] 
                            # spentBUSD = response['cummulativeQuoteQty']
                            # Place Sell order
                            logging.info(f"placing a sell order of {order_symbol} orderID {order_id}") 
                            params =  calculate_sell_parameters(order_symbol, sell_timeframe, asset_list=asset_list, boughtQty=boughtQty, project_setting = project_settings)
                            logging.info(f"Sell: {params}")

                            # Try place order 
                            try: 
                                trade_outcome = binance_interaction.make_trade_with_params(params, project_settings)
                                logging.info(trade_outcome)
                                # trading success placed remove from trading_symbols 
                                trading_symbols.remove(order_symbol)
                                # removing order info: orderID & symbol
                                for i in range(len(trading_infos)): 
                                    if trading_infos[i]['symbol']== order_symbol: 
                                        del trading_infos[i]
                                logging.info("finish placing sell order")

                            except:
                                trade_outcome = False 
                                logging.info("Error placing selling order")
                else:
                    logging.info("not fulfill sellling criteria")
            
            else:
                logging.info('No traded stock yet.')
        
        # Wait for 1 second 
        logging.info("keep checking for new candle update..")
        time.sleep(1) 



# strategy
def strategy_two(timeframe, percentage_rise, quote_asset, project_settings, sell_timeframe, percent_sell_rise): 
    trading_symbols = [] 
    trading_infos = []
    selling_infos = []
    previous_time = 0 
    prev_sell_time = 0 
    while 1: 
        test_time = get_and_transform_binance_data(symbol ="BTCBUSD", timeframe=timeframe, number_of_candles=1)
        current_time = test_time.iloc[0]['time']
        if current_time != previous_time: 
            logging.info('NEW candle data detected')
            previous_time = current_time 


            logging.info("STEP1. Cancelling open orders")
            # Get a list of open trades 
            open_trades = binance_interaction.query_open_trades(project_settings=project_settings)
            # iterate thorough list 
            for trades in open_trades: 
                executed_qty = float(trades['executedQty'])
                side = trades['side']

                if executed_qty == 0 and side == "BUY":
                    # Not filled BUY orders cancel 
                    binance_interaction.cancel_order_by_symbol(trades['symbol'], project_settings)
                    logging.info("Order Canceled")
                    trading_symbols.remove(trades['symbol'])
                    # removing order info: orderID & symbol
                    for i in range(len(trading_infos)): 
                        if trading_infos[i]['symbol']==trades['symbol']: 
                            del trading_infos[i]

                elif executed_qty == 0 and side == "SELL":
                    # Not filled SELL orders cancel 
                    binance_interaction.cancel_order_by_symbol(trades['symbol'], project_settings)
                    logging.info("Order Canceled")
                    # removing selling order info: orderID & symbol
                    for i in range(len(selling_infos)): 
                        if selling_infos[i]['symbol']==trades['symbol']: 
                            del selling_infos[i]
                    

            # Iterate through previous Sell orders. If FILLED then remove from trading list and selling order. 
            for Sellorder in selling_infos: 
                sellOrderId = Sellorder['sellOrderId']
                response = binance_interaction.check_order_by_symbol_id(order_symbol, sellOrderId, project_settings)
                logging.info(response)
                if response['status'] == "FILLED": 
                    # remove from selling_infos
                    for i in range(len(selling_infos)): 
                        if selling_infos[i]['symbol']==trades['symbol']: 
                            del selling_infos[i]
                     
                    # remove from trading_infos
                    for i in range(len(trading_infos)): 
                        if trading_infos[i]['symbol']==trades['symbol']: 
                            del trading_infos[i]
                    
                    # remove from trading symbol 
                    trading_symbols.remove(trades['symbol'])
            
            # Step 2. find new assets to purchase 
            logging.info("STEP2. Analyzing New Assets to purchase")
            asset_list = binance_interaction.query_quote_asset_list(quote_asset_symbol=quote_asset)
            # # wether buy or not. buy trading strategy 3 conseccutive growth. 
            new_trading_symbols = ['BTCBUSD','ETHBUSD'] 
            
            # see if symbols are already traded 
            for symbol in new_trading_symbols:
                if symbol not in trading_symbols:
                    # If symbol not already being traed, calculated the trading parameters 
                    logging.info(f"Opening trade on new symbol: {symbol}")
                    trade_parameters = calculate_trade_parameters(symbol, timeframe, asset_list=asset_list, project_setting=project_settings)

                    # make a trade
                    try: 
                        trade_outcome = binance_interaction.make_trade_with_params(trade_parameters, project_settings)
                        logging.info(trade_outcome)
                        # trading success placed added to trading_symbols 
                        trading_symbols.append(symbol)
                        trading_infos.append({"orderId": trade_outcome["orderId"], "symbol": symbol } )
                    
                    except:
                        trade_outcome = False 
                        logging.info("Error placing order")
                        logging.info(f"Error:{trade_outcome}")

            logging.info("Analysis Completed") 

        # Analysis SELLING condition 2 , Sell markets when 2 executive growth rate < 5%
         
        test_time = get_and_transform_binance_data(symbol ="BTCBUSD", timeframe=sell_timeframe, number_of_candles=1)
        sell_current_time = test_time.iloc[0]['time']
        if sell_current_time != prev_sell_time: 
            logging.info("A new half hour candle!")
            logging.info("STEP3. Start Analysis Selling condition") 
            prev_sell_time = sell_current_time

            if trading_infos: 
                # Identify all preivous traded symbols ordered are filled "trading symobls"
                for trade_info in trading_infos:
                    order_id = trade_info['orderId']
                    order_symbol = trade_info['symbol']
                    # Check if symbol pass rate is lower than 5% 
                    logging.info(f"analyze to sell {order_symbol} ...")
                    analysis_sell = determine_sell_event(order_symbol, timeframe = sell_timeframe, percentage_rise = percent_sell_rise) 
                    logging.info(f"analysis_sell: {analysis_sell}")
                    if analysis_sell: 
                        # Check if order is filled 
                        response = binance_interaction.check_order_by_symbol_id(order_symbol, order_id, project_settings)
                        logging.info(response)
                        if response['status'] == "FILLED":
                            boughtQty = response['executedQty'] 
                            # spentBUSD = response['cummulativeQuoteQty']
                            # Place Sell order
                            logging.info(f"placing a sell order of {order_symbol} orderID {order_id}") 
                            params =  calculate_sell_parameters(order_symbol, sell_timeframe, asset_list=asset_list, boughtQty=boughtQty, project_setting = project_settings)
                            logging.info(f"Sell: {params}")
                            # Try place order 
                            try: 
                                trade_outcome = binance_interaction.make_trade_with_params(params, project_settings)
                                logging.info(f"Trade_placing:{trade_outcome}")
                                sellOrderId = trade_outcome['orderId']
                                selling_infos.append({"symbol": order_symbol, "sellOrderId": sellOrderId})
                                logging.info("-------------Finish placing sell order--------------")

                            except:
                                trade_outcome = False 
                                logging.error("Error placing selling order")
                        else: 
                            logging.warning("Order is not filled")
                if len(selling_infos) == len(new_trading_symbols):
                    logging.info('Placed ALL selling orders.')
                    break
            else:
                logging.info('No traded stock yet.')
        
        # Wait for 1 second 
        logging.info("Will keep updating candle data...")
        time.sleep(1) 


