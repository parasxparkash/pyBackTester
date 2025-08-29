"""
Main backtesting engine for the PyAlgoTrader framework.

This module provides the main backtesting engine that coordinates
all components of the backtesting framework.
"""

import queue
import time
from pybacktester.data import HistoricCSVDataHandler
from pybacktester.portfolio import NaivePortfolio
from pybacktester.execution import SimulatedExecutionHandler
from pybacktester.performance import PerformanceAnalyzer


class Backtester:
    """
    Enscapsulates the settings and components for carrying out
    an event-driven backtest.
    """
    
    def __init__(self, csv_dir, symbol_list, initial_capital, start_date, 
                 data_handler=HistoricCSVDataHandler, 
                 execution_handler=SimulatedExecutionHandler,
                 portfolio=NaivePortfolio, strategy=None):
        """
        Initializes the backtester.

        Parameters:
        csv_dir - The hard root path to the CSV data directory.
        symbol_list - The list of symbol strings.
        initial_capital - The starting capital for the portfolio.
        start_date - The start datetime of the strategy.
        data_handler - (Class) Handles the market data feed.
        execution_handler - (Class) Handles the orders/fills for trades.
        portfolio - (Class) Keeps track of portfolio current and prior positions.
        strategy - (Class) Generates signals based on market data.
        """
        self.csv_dir = csv_dir
        self.symbol_list = symbol_list
        self.initial_capital = initial_capital
        self.start_date = start_date
        
        self.data_handler = data_handler
        self.execution_handler = execution_handler
        self.portfolio = portfolio
        self.strategy = strategy
        
        self.events = queue.Queue()
        
        self.signals = 0
        self.orders = 0
        self.fills = 0
        self.num_strats = 1
       
        self._generate_trading_instances()
    
    def _generate_trading_instances(self):
        """
        Generates the trading instance objects from 
        their class types.
        """
        print("Creating DataHandler, Strategy, Portfolio and ExecutionHandler")
        self.data_handler = self.data_handler(self.events, self.csv_dir, self.symbol_list)
        self.strategy = self.strategy(self.data_handler, self.events)
        self.portfolio = self.portfolio(self.data_handler, self.events, self.start_date, 
                                        self.initial_capital)
        self.execution_handler = self.execution_handler(self.events, self.data_handler)
    
    def _run_backtest(self):
        """
        Executes the backtest.
        """
        i = 0
        while True:
            i += 1
            print(f"{i}", end="\r")
            
            # Update the market bars
            if self.data_handler.continue_backtest == True:
                self.data_handler.update_bars()
            else:
                break
            
            # Handle the events
            while True:
                try:
                    event = self.events.get(False)
                except queue.Empty:
                    break
                else:
                    if event is not None:
                        if event.type == 'MARKET':
                            self.strategy.calculate_signals(event)
                            self.portfolio.update_timeindex(event)
                            
                        elif event.type == 'SIGNAL':
                            self.signals += 1
                            self.portfolio.update_signal(event)
                            
                        elif event.type == 'ORDER':
                            self.orders += 1
                            self.execution_handler.execute_order(event)
                            
                        elif event.type == 'FILL':
                            self.fills += 1
                            self.portfolio.update_fill(event)
            
            # Print the current holdings
            if i % 1000 == 0:
                print(f"Current portfolio value: {self.portfolio.current_holdings['total']}")
    
    def _output_performance(self):
        """
        Outputs the strategy performance from the backtest.
        """
        self.performance_analyzer = PerformanceAnalyzer(self.portfolio)
        stats = self.performance_analyzer.get_summary_stats()
        
        print("\nPerformance Metrics:")
        print("=" * 30)
        for metric, value in stats.items():
            if isinstance(value, float):
                print(f"{metric}: {value:.2f}")
            else:
                print(f"{metric}: {value}")
        
        print("\nCreating equity curve plot...")
        self.performance_analyzer.plot_equity_curve('equity_curve.png')
        print("Equity curve saved as 'equity_curve.png'")
        
        return stats
    
    def run(self):
        """
        Runs the backtest and outputs performance metrics.
        """
        print("Running Backtest...")
        t0 = time.time()
        self._run_backtest()
        t1 = time.time()
        print(f"\nBacktest complete in {t1-t0:.2f} seconds")
        print(f"Signals: {self.signals}")
        print(f"Orders: {self.orders}")
        print(f"Fills: {self.fills}")
        
        return self._output_performance()
    
    def get_portfolio(self):
        """
        Returns the portfolio object.
        """
        return self.portfolio
    
    def get_performance_analyzer(self):
        """
        Returns the performance analyzer object.
        """
        return self.performance_analyzer
