"""
Execution handler for the backtesting framework.

This module simulates the execution of orders in a realistic manner,
generating fill events based on market data.
"""

import datetime
from abc import ABC, abstractmethod
from pybacktester.event import FillEvent


class ExecutionHandler(ABC):
    """
    Abstract base class for execution handlers.
    """
    
    @abstractmethod
    def execute_order(self, event):
        """
        Takes an Order event and executes it, producing
        a Fill event that gets placed onto the events queue.

        Parameters:
        event - Contains an Event object with order information.
        """
        raise NotImplementedError("Should implement execute_order()")


class SimulatedExecutionHandler(ExecutionHandler):
    """
    The simulated execution handler simply converts all order
    objects into their equivalent fill objects automatically
    without latency, slippage or fill ratio issues.

    This allows a straightforward "first go" test of any strategy,
    before implementation with a more sophisticated execution
    handler.
    """
    
    def __init__(self, events, bars=None):
        """
        Initializes the handler, setting the event queues
        up internally.

        Parameters:
        events - The Queue of Event objects.
        bars - The DataHandler object that provides bar information (optional)
        """
        self.events = events
        self.bars = bars
    
    def execute_order(self, event):
        """
        Simply converts Order objects into Fill objects naively,
        i.e. without any latency, slippage or fill ratio problems.

        Parameters:
        event - Contains an Event object with order information.
        """
        if event.type == 'ORDER':
            # Get the current market price if available
            fill_cost = 75.0  # Default price
            if self.bars is not None:
                try:
                    bars = self.bars.get_latest_bars(event.symbol, N=1)
                    if bars and len(bars) > 0:
                        # Use the close price from the latest bar
                        fill_cost = bars[0][4]  # Close price
                except Exception:
                    # If we can't get the price, use the default
                    pass
            
            fill_event = FillEvent(
                datetime.datetime.utcnow(), event.symbol,
                'ARCA', event.quantity, event.direction, fill_cost
            )
            self.events.put(fill_event)
