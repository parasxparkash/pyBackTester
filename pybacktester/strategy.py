"""
Strategy base class for the backtesting framework.

This module provides an abstract base class for trading strategies
that can be implemented by users of the framework.
"""

from abc import ABC, abstractmethod


class Strategy(ABC):
    """
    Abstract base class for trading strategies.
    """
    
    def __init__(self, bars, events):
        """
        Initializes the strategy.
        
        Parameters:
        bars - The DataHandler object that provides bar information
        events - The event queue object
        """
        self.bars = bars
        self.events = events
        self.symbol_list = self.bars.symbol_list
    
    @abstractmethod
    def calculate_signals(self, event):
        """
        Provides the mechanisms to calculate the list of signals.
        
        Parameters:
        event - An Event object
        """
        raise NotImplementedError("Should implement calculate_signals()")
