"""
Yahoo Finance data handler for the backtesting framework.

This module provides functionality to fetch market data from Yahoo Finance
and process it for use in the backtesting framework.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pybacktester.data import DataHandler
from pybacktester.event import MarketEvent


class YahooFinanceDataHandler(DataHandler):
    """
    Yahoo Finance data handler that fetches data from Yahoo Finance API.
    """
    
    def __init__(self, events, csv_dir, symbol_list, start_date=None):
        """
        Initializes the Yahoo Finance data handler.
        
        Parameters:
        events - The event queue object
        csv_dir - CSV directory (not used for Yahoo Finance)
        symbol_list - A list of symbol strings
        start_date - The start date for fetching data (datetime object)
        """
        super().__init__(events)
        
        self.csv_dir = csv_dir
        self.symbol_list = symbol_list
        self.start_date = start_date if start_date else datetime(2020, 1, 1)
        self.end_date = datetime.now()
        
        self.symbol_data = {}
        self.latest_symbol_data = {}
        self.continue_backtest = True
        self.current_index = 0
        
        self._fetch_data()
    
    def _fetch_data(self):
        """
        Fetches data from Yahoo Finance for all symbols.
        """
        print("Fetching data from Yahoo Finance...")
        
        for symbol in self.symbol_list:
            print(f"Fetching data for {symbol}...")
            try:
                # Fetch data from Yahoo Finance
                ticker = yf.Ticker(symbol)
                data = ticker.history(start=self.start_date, end=self.end_date)
                
                if data.empty:
                    print(f"No data found for {symbol}")
                    continue
                
                # Convert to the format expected by the framework
                data.reset_index(inplace=True)
                print(f"Columns in fetched data: {data.columns.tolist()}")
                
                # Handle column names (they might be different)
                column_mapping = {
                    'Date': 'datetime',
                    'Open': 'open',
                    'High': 'high',
                    'Low': 'low',
                    'Close': 'close',
                    'Adj Close': 'adj_close',
                    'Volume': 'volume'
                }
                
                # Only rename columns that exist
                existing_columns = {k: v for k, v in column_mapping.items() if k in data.columns}
                data.rename(columns=existing_columns, inplace=True)
                
                # Convert timezone-aware datetime to timezone-naive
                if hasattr(data['datetime'].dt, 'tz') and data['datetime'].dt.tz is not None:
                    data['datetime'] = data['datetime'].dt.tz_localize(None)
                
                # Add missing columns if needed
                if 'adj_close' not in data.columns and 'close' in data.columns:
                    data['adj_close'] = data['close']
                
                # Sort by datetime
                data.sort_values('datetime', inplace=True)
                data.reset_index(drop=True, inplace=True)
                
                # Convert to list for sequential access
                self.symbol_data[symbol] = list(data.iterrows())
                self.latest_symbol_data[symbol] = []
                self.current_index = 0
                
            except Exception as e:
                print(f"Error fetching data for {symbol}: {e}")
        
        print("Data fetching complete.")
    
    def get_latest_bars(self, symbol, N=1):
        """
        Returns the last N bars from the latest_symbol list,
        or fewer if less bars are available.
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print(f"That symbol is not available in the historical data set.")
            raise
        else:
            return bars_list[-N:] if bars_list else []
    
    def update_bars(self):
        """
        Pushes the latest bar to the latest symbol structure
        for all symbols in the symbol list.
        """
        if not self.symbol_data:
            self.continue_backtest = False
            return
            
        no_more_data = True  # Assume no more data for any symbol
        
        for symbol in self.symbol_list:
            if symbol in self.symbol_data and self.current_index < len(self.symbol_data[symbol]):
                try:
                    # Get the next row of data
                    row = self.symbol_data[symbol][self.current_index]
                    bar_data = (
                        row[1]['datetime'],
                        row[1]['open'],
                        row[1]['high'],
                        row[1]['low'],
                        row[1]['close'],
                        row[1]['adj_close'],
                        row[1]['volume']
                    )
                    self.latest_symbol_data[symbol].append(bar_data)
                    no_more_data = False  # We still have data for at least one symbol
                except Exception as e:
                    print(f"Error processing data for {symbol}: {e}")
                    pass
        
        # Increment the current index
        self.current_index += 1
        
        # Continue backtest only if we have data for at least one symbol
        self.continue_backtest = not no_more_data
        
        if self.continue_backtest:
            self.events.put(MarketEvent())


def fetch_yahoo_finance_data(symbol, start_date, end_date=None):
    """
    Helper function to fetch data for a single symbol from Yahoo Finance.
    
    Parameters:
    symbol - The symbol to fetch data for
    start_date - The start date for fetching data (datetime object or string)
    end_date - The end date for fetching data (datetime object or string, defaults to today)
    
    Returns:
    DataFrame with the fetched data
    """
    if end_date is None:
        end_date = datetime.now()
    
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(start=start_date, end=end_date)
        return data
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return pd.DataFrame()
