"""
Example script demonstrating how to use the PyAlgoTrader framework.
"""

import datetime
import os
import sys

# Add the pybacktester directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'pybacktester'))

# Import framework components
from pybacktester.backtester import Backtester
from pybacktester.strategies import BuyAndHoldStrategy, MovingAverageCrossStrategy


def create_sample_data():
    """Create sample CSV data for testing."""
    # Create sample data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Create sample AAPL data
    sample_data = """Date,Open,High,Low,Close,Adj Close,Volume
2020-01-02,74.059998,75.150002,73.799999,75.089996,74.397125,135480400
2020-01-03,74.760002,75.470001,74.680000,75.110001,74.416916,146322800
2020-01-06,74.949997,75.980003,74.919998,75.580002,74.82690,118387200
2020-01-07,75.629997,75.980003,75.000000,75.20001,74.526733,108872000
2020-01-08,75.410004,76.40002,75.370003,76.260002,75.53970,132079200
2020-01-09,76.769997,77.309998,76.55003,77.029999,76.315918,135159600
2020-01-10,77.010002,77.16998,76.620003,76.820000,76.107971,117844000
2020-01-13,76.910004,77.300003,76.559998,77.239998,76.524391,108772800
2020-01-14,77.339996,77.860001,77.059998,77.59998,76.841835,121196800
2020-01-15,77.59998,78.239998,77.300003,78.169998,77.446953,113876800
"""
    
    with open('data/AAPL.csv', 'w') as f:
        f.write(sample_data)
    
    print("Sample data created in 'data/AAPL.csv'")


def run_example_backtest():
    """Run an example backtest."""
    print("Running example backtest with Buy and Hold strategy...")
    
    # Configuration
    csv_dir = 'data'
    symbol_list = ['AAPL']
    initial_capital = 100000.0
    start_date = datetime.datetime(2020, 1, 1, 0, 0, 0)
    
    # Create backtester
    backtester = Backtester(
        csv_dir=csv_dir,
        symbol_list=symbol_list,
        initial_capital=initial_capital,
        start_date=start_date,
        strategy=BuyAndHoldStrategy
    )
    
    # Run backtest
    try:
        results = backtester.run()
        print("\nBacktest completed successfully!")
        return results
    except Exception as e:
        print(f"Error running backtest: {e}")
        return None


if __name__ == "__main__":
    print("PyAlgoTrader Example Usage")
    print("=" * 30)
    
    # Create sample data
    create_sample_data()
    
    # Run example backtest
    results = run_example_backtest()
    
    if results:
        print("\nPerformance Summary:")
        print("-" * 20)
        for metric, value in results.items():
            if isinstance(value, float):
                print(f"{metric}: {value:.2f}")
            else:
                print(f"{metric}: {value}")
    
    print("\nTo run with your own data:")
    print("1. Place CSV files in the 'data' directory")
    print("2. Update symbol_list in the script")
    print("3. Run the script again")
