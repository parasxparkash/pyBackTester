"""
Example trading strategies for the backtesting framework.

This module provides example implementations of trading strategies
that can be used with the backtesting framework.
"""

import datetime
import numpy as np
from pybacktester.strategy import Strategy
from pybacktester.event import SignalEvent


class BuyAndHoldStrategy(Strategy):
    """
    This is an extremely simple strategy that goes LONG all of the
    symbols as soon as a bar is received and never exits.
    """
    
    def __init__(self, bars, events):
        """
        Initializes the buy and hold strategy.

        Parameters:
        bars - The DataHandler object that provides bar information
        events - The Event Queue object
        """
        super().__init__(bars, events)
        
        # Once buy & hold signal is given, these are set to True
        self.bought = self._calculate_initial_bought()
    
    def _calculate_initial_bought(self):
        """
        Adds keys to the bought dictionary for all symbols
        and sets them to False.
        """
        bought = {}
        for s in self.symbol_list:
            bought[s] = False
        return bought
    
    def calculate_signals(self, event):
        """
        For "Buy and Hold" we generate a single signal per symbol
        and then no additional signals. This means we are
        constantly long the market from the date of strategy
        initialisation.

        Parameters:
        event - A MarketEvent object
        """
        if event.type == 'MARKET':
            for s in self.symbol_list:
                bars = self.bars.get_latest_bars(s, N=1)
                if bars is not None and len(bars) > 0:
                    if self.bought[s] == False:
                        # (Symbol, Datetime, Type = LONG, SHORT or EXIT)
                        signal = SignalEvent(1, s, datetime.datetime.utcnow(), 'LONG', 1.0)
                        self.events.put(signal)
                        self.bought[s] = True


class MovingAverageCrossStrategy(Strategy):
    """
    Carries out a basic Moving Average Crossover strategy with a
    short/long simple weighted moving average. Uses 9/26 periods.
    """
    
    def __init__(self, bars, events):
        """
        Initializes the Moving Average Cross Strategy with 9/26 periods.

        Parameters:
        bars - The DataHandler object that provides bar information
        events - The Event Queue object
        """
        super().__init__(bars, events)
        
        self.short_window = 9
        self.long_window = 26
        
        # Set to True if a symbol is in the market
        self.bought = self._calculate_initial_bought()
    
    def _calculate_initial_bought(self):
        """
        Adds keys to the bought dictionary for all symbols
        and sets them to 'OUT'.
        """
        bought = {}
        for s in self.symbol_list:
            bought[s] = 'OUT'
        return bought
    
    def calculate_signals(self, event):
        """
        Generates a new set of signals based on the Moving Average
        crossover strategy. Calculates the short and long simple moving
        averages. For a short window SMA greater than a long window SMA
        a LONG signal is generated, otherwise an EXIT signal is given.

        Parameters:
        event - A MarketEvent object
        """
        if event.type == 'MARKET':
            for s in self.symbol_list:
                bars = self.bars.get_latest_bars(s, N=self.long_window)
                
                if len(bars) >= self.long_window:
                    # Calculate the simple moving averages
                    short_sma = np.mean([bar[5] for bar in bars[-self.short_window:]])
                    long_sma = np.mean([bar[5] for bar in bars[-self.long_window:]])
                    
                    # Trading signals based on moving average crossover
                    if short_sma > long_sma and self.bought[s] == 'OUT':
                        signal = SignalEvent(1, s, datetime.datetime.utcnow(), 'LONG', 1.0)
                        self.events.put(signal)
                        self.bought[s] = 'LONG'
                    
                    elif short_sma < long_sma and self.bought[s] == 'LONG':
                        signal = SignalEvent(1, s, datetime.datetime.utcnow(), 'EXIT', 1.0)
                        self.events.put(signal)
                        self.bought[s] = 'OUT'
