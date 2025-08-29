"""
Performance analyzer for the backtesting framework.

This module calculates performance metrics and generates reports
for backtesting results.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


class PerformanceAnalyzer:
    """
    Performance analyzer for calculating metrics and generating reports.
    """
    
    def __init__(self, portfolio):
        """
        Initializes the performance analyzer.
        
        Parameters:
        portfolio - The portfolio object from the backtest
        """
        self.portfolio = portfolio
        self.equity_curve = self._create_equity_curve()
    
    def _create_equity_curve(self):
        """
        Creates an equity curve from the portfolio holdings.
        """
        curve = pd.DataFrame(self.portfolio.all_holdings)
        curve.set_index('datetime', inplace=True)
        curve['returns'] = curve['total'].pct_change()
        curve['equity_curve'] = (1.0 + curve['returns']).cumprod()
        return curve
    
    def calculate_sharpe_ratio(self, risk_free_rate=0.0):
        """
        Calculate the Sharpe ratio of the strategy.
        
        Parameters:
        risk_free_rate - The risk-free rate per annum
        
        Returns:
        Sharpe ratio
        """
        # Calculate the excess returns
        excess_returns = self.equity_curve['returns'] - risk_free_rate / 252
        
        # Calculate annualized Sharpe ratio
        sharpe_ratio = np.sqrt(252) * (excess_returns.mean() / excess_returns.std())
        return sharpe_ratio
    
    def calculate_max_drawdown(self):
        """
        Calculate the maximum drawdown of the strategy.
        
        Returns:
        Max drawdown, duration
        """
        # Calculate the cumulative returns curve and maximum cumulative returns curve
        cumulative = self.equity_curve['equity_curve']
        cumulative_max = cumulative.cummax()
        
        # Calculate the drawdowns
        drawdowns = (cumulative - cumulative_max) / cumulative_max
        
        # Calculate the max drawdown and duration
        max_drawdown = drawdowns.min()
        max_drawdown_duration = drawdowns.idxmin()
        
        return max_drawdown, max_drawdown_duration
    
    def calculate_cagr(self):
        """
        Calculate the Compound Annual Growth Rate (CAGR).
        
        Returns:
        CAGR
        """
        # Get the number of days in the strategy
        start_date = self.equity_curve.index[0]
        end_date = self.equity_curve.index[-1]
        days = (end_date - start_date).days
        
        # Calculate CAGR
        cagr = (self.equity_curve['equity_curve'].iloc[-1]) ** (365.0 / days) - 1
        return cagr
    
    def calculate_win_ratio(self):
        """
        Calculate the win ratio (percentage of profitable trades).
        
        Returns:
        Win ratio
        """
        if not hasattr(self.portfolio, 'all_trades') or not self.portfolio.all_trades:
            return 0.0
        
        profitable_trades = [trade for trade in self.portfolio.all_trades if trade['profit'] > 0]
        return len(profitable_trades) / len(self.portfolio.all_trades) * 100 if self.portfolio.all_trades else 0.0
    
    def calculate_profit_factor(self):
        """
        Calculate the profit factor (gross profit / gross loss).
        
        Returns:
        Profit factor
        """
        if not hasattr(self.portfolio, 'all_trades') or not self.portfolio.all_trades:
            return 0.0
        
        gross_profit = sum(trade['profit'] for trade in self.portfolio.all_trades if trade['profit'] > 0)
        gross_loss = abs(sum(trade['profit'] for trade in self.portfolio.all_trades if trade['profit'] < 0))
        
        return gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    def calculate_car_mdd(self):
        """
        Calculate CAR/MDD (Compound Annual Return to Maximum Drawdown).
        
        Returns:
        CAR/MDD ratio
        """
        cagr = self.calculate_cagr()
        max_dd, _ = self.calculate_max_drawdown()
        
        return cagr / abs(max_dd) if max_dd != 0 else float('inf')
    
    def calculate_ulcer_index(self):
        """
        Calculate the Ulcer Index (measures drawdown depth and duration).
        
        Returns:
        Ulcer Index
        """
        # Calculate the percentage drawdowns
        cumulative = self.equity_curve['equity_curve']
        cumulative_max = cumulative.cummax()
        drawdowns = (cumulative - cumulative_max) / cumulative_max * 100
        
        # Calculate the squared drawdowns
        squared_drawdowns = drawdowns ** 2
        
        # Calculate the average of squared drawdowns
        avg_squared_drawdowns = squared_drawdowns.mean()
        
        # Calculate the Ulcer Index
        ulcer_index = np.sqrt(avg_squared_drawdowns)
        return ulcer_index
    
    def calculate_expectancy(self):
        """
        Calculate expectancy (average profit/loss per trade).
        
        Returns:
        Expectancy
        """
        if not hasattr(self.portfolio, 'all_trades') or not self.portfolio.all_trades:
            return 0.0
        
        total_profit = sum(trade['profit'] for trade in self.portfolio.all_trades)
        return total_profit / len(self.portfolio.all_trades) if self.portfolio.all_trades else 0.0
    
    def calculate_sortino_ratio(self, risk_free_rate=0.0):
        """
        Calculate the Sortino ratio (risk-adjusted return penalizing downside volatility).
        
        Parameters:
        risk_free_rate - The risk-free rate per annum
        
        Returns:
        Sortino ratio
        """
        # Calculate the excess returns
        excess_returns = self.equity_curve['returns'] - risk_free_rate / 252
        
        # Calculate downside deviation (volatility of negative returns only)
        negative_returns = excess_returns[excess_returns < 0]
        downside_deviation = np.sqrt(252) * negative_returns.std()
        
        # Calculate annualized return
        annualized_return = (1 + excess_returns.mean()) ** 252 - 1
        
        # Calculate Sortino ratio
        sortino_ratio = annualized_return / downside_deviation if downside_deviation > 0 else float('inf')
        return sortino_ratio
    
    def calculate_downside_deviation(self):
        """
        Calculate downside deviation (volatility of negative returns only).
        
        Returns:
        Downside deviation
        """
        # Calculate downside deviation (volatility of negative returns only)
        negative_returns = self.equity_curve['returns'][self.equity_curve['returns'] < 0]
        downside_deviation = np.sqrt(252) * negative_returns.std()
        return downside_deviation
    
    def calculate_calmar_ratio(self):
        """
        Calculate Calmar ratio (annual return divided by max drawdown).
        
        Returns:
        Calmar ratio
        """
        cagr = self.calculate_cagr()
        max_dd, _ = self.calculate_max_drawdown()
        
        return cagr / abs(max_dd) if max_dd != 0 else float('inf')
    
    def calculate_recovery_factor(self):
        """
        Calculate recovery factor (net profit divided by max drawdown).
        
        Returns:
        Recovery factor
        """
        total_return = self.equity_curve['equity_curve'].iloc[-1] - 1.0
        max_dd, _ = self.calculate_max_drawdown()
        
        return total_return / abs(max_dd) if max_dd != 0 else float('inf')
    
    def calculate_gain_to_pain_ratio(self):
        """
        Calculate gain to pain ratio (total gains divided by total losses).
        
        Returns:
        Gain to pain ratio
        """
        positive_returns = self.equity_curve['returns'][self.equity_curve['returns'] > 0]
        negative_returns = self.equity_curve['returns'][self.equity_curve['returns'] < 0]
        
        total_gains = positive_returns.sum()
        total_losses = abs(negative_returns.sum())
        
        return total_gains / total_losses if total_losses > 0 else float('inf')
    
    def calculate_average_trade_net_profit(self):
        """
        Calculate average trade net profit.
        
        Returns:
        Average trade net profit
        """
        if not hasattr(self.portfolio, 'all_trades') or not self.portfolio.all_trades:
            return 0.0
        
        total_profit = sum(trade['profit'] for trade in self.portfolio.all_trades)
        return total_profit / len(self.portfolio.all_trades) if self.portfolio.all_trades else 0.0
    
    def calculate_payoff_ratio(self):
        """
        Calculate payoff ratio (average winning trade vs average losing trade).
        
        Returns:
        Payoff ratio
        """
        if not hasattr(self.portfolio, 'all_trades') or not self.portfolio.all_trades:
            return 0.0
        
        winning_trades = [trade['profit'] for trade in self.portfolio.all_trades if trade['profit'] > 0]
        losing_trades = [abs(trade['profit']) for trade in self.portfolio.all_trades if trade['profit'] < 0]
        
        avg_winning = np.mean(winning_trades) if winning_trades else 0.0
        avg_losing = np.mean(losing_trades) if losing_trades else 0.0
        
        return avg_winning / avg_losing if avg_losing > 0 else float('inf')
    
    def calculate_average_winning_trade(self):
        """
        Calculate average winning trade.
        
        Returns:
        Average winning trade
        """
        if not hasattr(self.portfolio, 'all_trades') or not self.portfolio.all_trades:
            return 0.0
        
        winning_trades = [trade['profit'] for trade in self.portfolio.all_trades if trade['profit'] > 0]
        return np.mean(winning_trades) if winning_trades else 0.0
    
    def calculate_average_losing_trade(self):
        """
        Calculate average losing trade.
        
        Returns:
        Average losing trade
        """
        if not hasattr(self.portfolio, 'all_trades') or not self.portfolio.all_trades:
            return 0.0
        
        losing_trades = [abs(trade['profit']) for trade in self.portfolio.all_trades if trade['profit'] < 0]
        return np.mean(losing_trades) if losing_trades else 0.0
    
    def get_summary_stats(self):
        """
        Get a summary of all performance statistics.
        
        Returns:
        Dictionary of performance statistics
        """
        stats = {}
        stats['Total Return'] = (self.equity_curve['equity_curve'].iloc[-1] - 1.0) * 100
        stats['Sharpe Ratio'] = self.calculate_sharpe_ratio()
        stats['Max Drawdown'], _ = self.calculate_max_drawdown()
        stats['Max Drawdown %'] = stats['Max Drawdown'] * 100
        stats['CAGR'] = self.calculate_cagr() * 100
        stats['Volatility'] = self.equity_curve['returns'].std() * np.sqrt(252) * 100
        stats['Win Ratio'] = self.calculate_win_ratio()
        stats['CAR/MDD'] = self.calculate_car_mdd()
        stats['Ulcer Index'] = self.calculate_ulcer_index()
        stats['Expectancy'] = self.calculate_expectancy()
        stats['Sortino Ratio'] = self.calculate_sortino_ratio()
        stats['Downside Deviation'] = self.calculate_downside_deviation()
        stats['Calmar Ratio'] = self.calculate_calmar_ratio()
        stats['Recovery Factor'] = self.calculate_recovery_factor()
        stats['Gain to Pain Ratio'] = self.calculate_gain_to_pain_ratio()
        stats['Average Trade Net Profit'] = self.calculate_average_trade_net_profit()
        stats['Average Winning Trade'] = self.calculate_average_winning_trade()
        stats['Average Losing Trade'] = self.calculate_average_losing_trade()
        
        return stats
    
    def plot_equity_curve(self, filename='equity_curve.png'):
        """
        Plot the equity curve and save to file.
        
        Parameters:
        filename - The filename to save the plot to
        """
        plt.figure(figsize=(10, 6))
        plt.plot(self.equity_curve.index, self.equity_curve['equity_curve'])
        plt.title('Equity Curve')
        plt.xlabel('Date')
        plt.ylabel('Cumulative Returns')
        plt.grid(True)
        plt.savefig(filename)
        plt.close()
