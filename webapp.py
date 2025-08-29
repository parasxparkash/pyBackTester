"""
Web application for PyBacktester.

This module provides a web interface to run backtests and visualize results.
"""

import os
import sys
import json
import base64
from io import BytesIO
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Add the pybacktester directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'pybacktester'))

from pybacktester.backtester import Backtester
from pybacktester.yfinance_data import YahooFinanceDataHandler
from pybacktester.strategies import BuyAndHoldStrategy, MovingAverageCrossStrategy


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'


@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')


@app.route('/run_backtest', methods=['POST'])
def run_backtest():
    """Run a backtest and return the results."""
    try:
        # Get parameters from the request
        data = request.get_json()
        symbols = data.get('symbols', 'AAPL').split(',')
        symbols = [s.strip() for s in symbols]
        strategy_name = data.get('strategy', 'buy_and_hold')
        start_date_str = data.get('start_date', '2020-01-01')
        initial_capital = float(data.get('initial_capital', 1000))
        
        # Parse start date
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        
        # Select strategy
        if strategy_name == 'moving_average':
            strategy = MovingAverageCrossStrategy
            strategy_label = 'Moving Average Crossover'
            # Create a temporary instance to get parameters
            temp_strategy = strategy.__new__(strategy)
            temp_strategy.short_window = 9
            temp_strategy.long_window = 26
            strategy_params = {
                'short_window': temp_strategy.short_window,
                'long_window': temp_strategy.long_window
            }
        else:
            strategy = BuyAndHoldStrategy
            strategy_label = 'Buy and Hold'
            strategy_params = {}
        
        # Create backtester with Yahoo Finance data
        backtester = Backtester(
            csv_dir=None,  # Not used with Yahoo Finance data
            symbol_list=symbols,
            initial_capital=initial_capital,
            start_date=start_date,
            data_handler=YahooFinanceDataHandler,
            strategy=strategy
        )
        
        # Run backtest
        results = backtester.run()
        
        # Get performance analyzer
        performance_analyzer = backtester.get_performance_analyzer()
        
        # Get data information
        data_handler = backtester.data_handler
        data_points = len(performance_analyzer.equity_curve)
        
        # Calculate data statistics
        data_stats = {}
        for symbol in symbols:
            if hasattr(data_handler, 'symbol_data') and symbol in data_handler.symbol_data:
                # For Yahoo Finance data handler
                symbol_data = data_handler.latest_symbol_data[symbol]
                if symbol_data:
                    closes = [bar[4] for bar in symbol_data]  # Close prices
                    highs = [bar[2] for bar in symbol_data]   # High prices
                    lows = [bar[3] for bar in symbol_data]    # Low prices
                    volumes = [bar[6] for bar in symbol_data] # Volume
                    
                    # Calculate additional statistics
                    returns = np.diff(closes) / closes[:-1]  # Daily returns
                    
                    data_stats[symbol] = {
                        'count': len(closes),
                        'price_mean': float(np.mean(closes)),
                        'price_std': float(np.std(closes)),
                        'price_min': float(np.min(closes)),
                        'price_max': float(np.max(closes)),
                        'high_mean': float(np.mean(highs)),
                        'high_std': float(np.std(highs)),
                        'high_min': float(np.min(highs)),
                        'high_max': float(np.max(highs)),
                        'low_mean': float(np.mean(lows)),
                        'low_std': float(np.std(lows)),
                        'low_min': float(np.min(lows)),
                        'low_max': float(np.max(lows)),
                        'volume_mean': float(np.mean(volumes)),
                        'volume_std': float(np.std(volumes)),
                        'volume_min': float(np.min(volumes)),
                        'volume_max': float(np.max(volumes)),
                        'return_mean': float(np.mean(returns) * 100),  # Convert to percentage
                        'return_std': float(np.std(returns) * 100),   # Convert to percentage
                        'return_min': float(np.min(returns) * 100),   # Convert to percentage
                        'return_max': float(np.max(returns) * 100)    # Convert to percentage
                    }
        
        data_info = {
            'symbols': symbols,
            'start_date': start_date_str,
            'initial_capital': initial_capital,
            'data_points': data_points,
            'data_stats': data_stats
        }
        
        # Create enhanced equity curve plot with drawdown
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12), gridspec_kw={'height_ratios': [3, 1]})
        
        # Plot equity curve
        ax1.plot(performance_analyzer.equity_curve.index, 
                performance_analyzer.equity_curve['equity_curve'], 
                label='Equity Curve', color='blue', linewidth=2)
        ax1.set_title('Equity Curve', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Cumulative Returns', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Calculate and plot drawdown
        cumulative = performance_analyzer.equity_curve['equity_curve']
        cumulative_max = cumulative.cummax()
        drawdown = (cumulative - cumulative_max) / cumulative_max * 100
        ax2.fill_between(performance_analyzer.equity_curve.index, drawdown, 0, alpha=0.3, color='red')
        ax2.plot(performance_analyzer.equity_curve.index, drawdown, color='red', linewidth=1)
        ax2.set_title('Drawdown Analysis', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Drawdown (%)', fontsize=12)
        ax2.grid(True, alpha=0.3)
        ax2.set_xlabel('Date', fontsize=12)
        
        # Add max drawdown annotation
        max_dd_idx = drawdown.idxmin()
        max_dd_val = drawdown.min()
        ax2.annotate(f'Max DD: {max_dd_val:.2f}%', 
                    xy=(max_dd_idx, max_dd_val),
                    xytext=(10, 10),
                    textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
        
        plt.tight_layout()
        
        # Save plot to base64 string
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)
        plot_url = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()
        
        # Format results for JSON serialization
        formatted_results = {}
        for key, value in results.items():
            if isinstance(value, np.float64) or isinstance(value, np.int64) or isinstance(value, np.float32):
                # Handle special float values that are not JSON serializable
                if np.isinf(value) or np.isnan(value):
                    # Skip infinity and NaN values
                    continue
                else:
                    formatted_results[key] = float(value)
            elif isinstance(value, pd.Timestamp):
                formatted_results[key] = str(value)
            else:
                formatted_results[key] = value
        
        # Add additional information
        additional_info = {
            'strategy_name': strategy_label,
            'strategy_params': strategy_params,
            'data_info': data_info
        }
        
        return jsonify({
            'success': True,
            'results': formatted_results,
            'additional_info': additional_info,
            'plot': plot_url
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/strategies')
def get_strategies():
    """Return a list of available strategies."""
    strategies = [
        {'name': 'buy_and_hold', 'label': 'Buy and Hold'},
        {'name': 'moving_average', 'label': 'Moving Average Crossover'}
    ]
    return jsonify(strategies)


if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=8000)
