"""
Portfolio manager for the backtesting framework.

This module handles position management, risk calculations,
and generates order signals based on strategy signals.
"""

import datetime
from math import floor
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from pybacktester.event import OrderEvent


class Portfolio(ABC):
    """
    Abstract base class for portfolio managers.
    """
    
    def __init__(self, bars, events, start_date, initial_capital=100000.0):
        """
        Initializes the portfolio.
        
        Parameters:
        bars - The DataHandler object that provides bar information
        events - The event queue object
        start_date - The start date of the portfolio
        initial_capital - The starting capital for the portfolio
        """
        self.bars = bars
        self.events = events
        self.symbol_list = self.bars.symbol_list
        self.start_date = start_date
        self.initial_capital = initial_capital
        
        self.all_positions = self.construct_all_positions()
        self.current_positions = dict((k, v) for k, v in 
                                      [(s, 0) for s in self.symbol_list])
        
        self.all_holdings = self.construct_all_holdings()
        self.current_holdings = self.construct_current_holdings()
    
    def construct_all_positions(self):
        """
        Constructs the positions list using start_date
        to determine when the time index will begin.
        """
        d = dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])
        d['datetime'] = self.start_date
        return [d]
    
    def construct_all_holdings(self):
        """
        Constructs the holdings list using start_date
        to determine when the time index will begin.
        """
        d = dict((k, v) for k, v in [(s, 0.0) for s in self.symbol_list])
        d['datetime'] = self.start_date
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return [d]
    
    def construct_current_holdings(self):
        """
        This constructs the dictionary which will hold the instantaneous
        value of the portfolio across all symbols.
        """
        d = dict((k, v) for k, v in [(s, 0.0) for s in self.symbol_list])
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return d
    
    @abstractmethod
    def update_signal(self, event):
        """
        Acts on a SignalEvent to generate new orders
        based on the portfolio logic.
        """
        raise NotImplementedError("Should implement update_signal()")
    
    @abstractmethod
    def update_fill(self, event):
        """
        Updates the portfolio current positions and holdings
        from a FillEvent.
        """
        raise NotImplementedError("Should implement update_fill()")
    
    def update_timeindex(self, event):
        """
        Adds a new record to the positions matrix for the current
        market data bar. This reflects the PREVIOUS bar, i.e. all
        current market data at this stage is known (OHLCV).
        """
        bars = self.bars.get_latest_bars(self.symbol_list[0])
        if not bars:
            return
            
        latest_datetime = bars[0][0]
        
        # Update positions
        dp = dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])
        dp['datetime'] = latest_datetime
        
        for s in self.symbol_list:
            dp[s] = self.current_positions[s]
        
        # Append the current positions
        self.all_positions.append(dp)
        
        # Update holdings
        dh = dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])
        dh['datetime'] = latest_datetime
        dh['cash'] = self.current_holdings['cash']
        dh['commission'] = self.current_holdings['commission']
        
        # Calculate total value based on current market prices
        total_value = self.current_holdings['cash'] - self.current_holdings['commission']
        for s in self.symbol_list:
            # Get current market value based on positions and latest price
            bars = self.bars.get_latest_bars(s)
            if bars:
                market_value = self.current_positions[s] * bars[0][5]  # Using adj_close
                dh[s] = market_value
                total_value += market_value
        
        dh['total'] = total_value
        
        # Update current_holdings with the new total
        self.current_holdings['total'] = total_value
        
        # Append the current holdings
        self.all_holdings.append(dh)


class NaivePortfolio(Portfolio):
    """
    The NaivePortfolio object is designed to send orders to
    a brokerage object with a constant quantity size blindly,
    i.e. without any risk management or position sizing. It is
    used to test simpler strategies such as BuyAndHold.
    """
    
    def __init__(self, bars, events, start_date, initial_capital=100000.0):
        """
        Initializes the portfolio with data and an event queue.
        Also includes a starting datetime index and initial capital.
        """
        super().__init__(bars, events, start_date, initial_capital)
        self.symbol_list = bars.symbol_list
        self.all_trades = []
    
    def update_signal(self, event):
        """
        Simply files an Order event as a constant quantity
        sizing of the signal object, without risk management or
        position sizing considerations.
        """
        if event.type == 'SIGNAL':
            order_event = OrderEvent(
                event.symbol, 'MKT', 100, event.signal_type
            )
            self.events.put(order_event)
    
    def update_fill(self, event):
        """
        Updates the portfolio current positions and holdings
        from a FillEvent.
        """
        if event.type == 'FILL':
            # Check whether the fill is a buy or sell
            fill_dir = 0
            if event.direction == 'BUY':
                fill_dir = 1
            elif event.direction == 'SELL':
                fill_dir = -1
            else:
                # Default to BUY for unknown directions
                fill_dir = 1
            
            # Calculate profit/loss for this trade
            # This is a simplified calculation - in a real system, you'd track entry prices
            profit = 0
            if hasattr(self, '_last_fill_price') and event.symbol in self._last_fill_price:
                # Calculate profit based on price difference
                if fill_dir == -1:  # Sell order
                    profit = (event.fill_cost - self._last_fill_price[event.symbol]) * event.quantity
                elif fill_dir == 1:  # Buy order
                    if self.current_positions[event.symbol] < 0:  # Closing a short position
                        profit = (self._last_fill_price[event.symbol] - event.fill_cost) * event.quantity
            
            # Store the fill price for profit calculation
            if not hasattr(self, '_last_fill_price'):
                self._last_fill_price = {}
            self._last_fill_price[event.symbol] = event.fill_cost
            
            # Record the trade
            trade = {
                'symbol': event.symbol,
                'direction': event.direction,
                'quantity': event.quantity,
                'price': event.fill_cost,
                'commission': event.commission,
                'profit': profit,
                'datetime': event.datetime
            }
            self.all_trades.append(trade)
            
            # Update positions list with new quantities
            self.current_positions[event.symbol] += fill_dir * event.quantity
            
            # Update cash and commission
            cost = event.fill_cost * event.quantity
            # For BUY, we subtract cash, for SELL we add cash
            self.current_holdings['cash'] -= fill_dir * cost
            self.current_holdings['commission'] += event.commission
            self.current_holdings['cash'] -= event.commission
            
            # Note: current_holdings[symbol] will be updated in update_timeindex
            # based on current market prices and positions, not here
