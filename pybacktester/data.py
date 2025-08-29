"""
Data handler for the backtesting framework.

This module provides functionality to handle market data, including
loading data from CSV files and providing an interface for the
backtesting engine to access price data.
"""

import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from pybacktester.event import MarketEvent


class DataHandler(ABC):
    """
    Abstract base class for data handlers.
    """
    
    def __init__(self, events):
        """
        Initializes the data handler.
        
        Parameters:
        events - The event queue object
        """
        self.events = events
    
    @abstractmethod
    def get_latest_bars(self, symbol, N=1):
        """
        Returns the last N bars from the latest_symbol list,
        or fewer if less bars are available.
        """
        raise NotImplementedError("Should implement get_latest_bars()")
    
    @abstractmethod
    def update_bars(self):
        """
        Pushes the latest bar to the latest symbol structure
        for all symbols in the symbol list.
        """
        raise NotImplementedError("Should implement update_bars()")


class HistoricCSVDataHandler(DataHandler):
    """
    Historic data handler that loads data from CSV files.
    """
    
    def __init__(self, events, csv_dir, symbol_list):
        """
        Initializes the historic data handler.
        
        Parameters:
        events - The event queue object
        csv_dir - Absolute directory path to the CSV data files
        symbol_list - A list of symbol strings
        """
        super().__init__(events)
        
        self.csv_dir = csv_dir
        self.symbol_list = symbol_list
        
        self.symbol_data = {}
        self.latest_symbol_data = {}
        self.continue_backtest = True
        
        self._open_convert_csv_files()
    
    def _open_convert_csv_files(self):
        """
        Opens the CSV files from the data directory, converting
        them into pandas DataFrames within a symbol dictionary.
        
        For this handler it is assumed that the data is
        taken from Yahoo Finance with headers:
        Date,Open,High,Low,Close,Adj Close,Volume
        """
        comb_index = None
        
        for s in self.symbol_list:
            # Load CSV file with no header information, indexed on date
            self.symbol_data[s] = pd.read_csv(
                f"{self.csv_dir}/{s}.csv",
                header=0, index_col=0, parse_dates=True,
                names=['datetime', 'open', 'high', 'low', 'close', 'adj_close', 'volume']
            ).sort_index()
            
            # Combine the index to pad forward values
            if comb_index is None:
                comb_index = self.symbol_data[s].index
            else:
                comb_index.union(self.symbol_data[s].index)
                
            # Set the latest symbol_data to None
            self.latest_symbol_data[s] = []
        
        # Reindex the dataframes
        for s in self.symbol_list:
            self.symbol_data[s] = self.symbol_data[s].reindex(index=comb_index, method='pad').iterrows()
    
    def _get_new_bar(self, symbol):
        """
        Returns the latest bar from the data feed as a tuple of
        (datetime, open, high, low, close, adj_close, volume).
        """
        for b in self.symbol_data[symbol]:
            yield b
    
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
            return bars_list[-N:]
    
    def update_bars(self):
        """
        Pushes the latest bar to the latest symbol structure
        for all symbols in the symbol list.
        """
        for s in self.symbol_list:
            try:
                bar = next(self.symbol_data[s])
                # bar is a tuple (timestamp, pandas.Series)
                bar_data = (bar[0], bar[1]['open'], bar[1]['high'], bar[1]['low'], 
                           bar[1]['close'], bar[1]['adj_close'], bar[1]['volume'])
                self.latest_symbol_data[s].append(bar_data)
            except StopIteration:
                self.continue_backtest = False
        if self.continue_backtest:
            self.events.put(MarketEvent())
