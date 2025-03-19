# PyBacktester - Event-Driven Backtesting Framework

A Python-based event-driven backtesting framework for algorithmic trading strategies.

## Features
- Event-driven architecture for realistic backtesting
- Support for multiple financial instruments
- Performance metrics and risk analysis
- Customizable trading strategies
- Order management system

## Components
1. Event System - Handles different types of events in the backtesting process
2. Data Handler - Processes market data
3. Strategy - Implements trading logic
4. Portfolio - Manages positions and risk
5. Execution - Simulates order execution
6. Performance - Calculates metrics and generates reports

## Installation
```bash
pip install -r requirements.txt
```

## Project Structure
```
PyBacktester/
├── pybacktester/
│   ├── __init__.py
│   ├── event.py          # Event classes
│   ├── data.py           # Data handler
│   ├── strategy.py       # Strategy base class
│   ├── strategies.py     # Example strategies
│   ├── portfolio.py      # Portfolio manager
│   ├── execution.py      # Execution handler
│   ├── performance.py    # Performance analyzer
│   └── backtester.py     # Main backtesting engine
├── data/                 # Market data (CSV files)
├── main.py               # Example usage
├── test_framework.py     # Unit tests
├── requirements.txt      # Dependencies
└── README.md
```

## Usage

### 1. Prepare Data
Create a `data` directory and add CSV files with OHLCV data for the symbols you want to test. The CSV files should have the following format:
```
Date,Open,High,Low,Close,Adj Close,Volume
2020-01-01,100.0,105.0,99.0,103.0,103.0,1000000
...
```

### 2. Create a Strategy
Extend the `Strategy` base class to implement your trading logic:

```python
from pybacktester.strategy import Strategy
from pybacktester.event import SignalEvent

class MyStrategy(Strategy):
    def __init__(self, bars, events):
        super().__init__(bars, events)
        # Initialize any strategy-specific variables
        
    def calculate_signals(self, event):
        if event.type == 'MARKET':
            # Implement your trading logic here
            # Generate SignalEvent objects and put them in self.events
            pass
```

### 3. Run a Backtest
```python
from pybacktester.backtester import Backtester
from my_strategy import MyStrategy  # Your custom strategy

# Configuration
csv_dir = 'data'
symbol_list = ['AAPL', 'GOOG']
initial_capital = 100000.0
start_date = datetime.datetime(2020, 1, 0, 0, 0)

# Create and run backtester
backtester = Backtester(
    csv_dir=csv_dir,
    symbol_list=symbol_list,
    initial_capital=initial_capital,
    start_date=start_date,
    strategy=MyStrategy
)

results = backtester.run()
```

### 4. Example Strategies
The framework includes two example strategies:
- `BuyAndHoldStrategy`: Buys and holds assets
- `MovingAverageCrossStrategy`: Moving average crossover strategy

## Running Tests
```bash
python test_framework.py
```

## Performance Metrics
The framework calculates the following performance metrics:
- Total Return
- Sharpe Ratio
- Maximum Drawdown
- CAGR (Compound Annual Growth Rate)
- Volatility

## Extending the Framework
You can extend the framework by:
1. Creating custom strategies
2. Implementing custom portfolio managers
3. Adding new execution handlers
4. Enhancing the performance analyzer

## License
This project is licensed under the MIT License.

# Updated on 2025-03-01 13:18:14

# Updated on 2025-03-01 21:03:56

# Updated on 2025-03-03 10:35:45

# Updated on 2025-03-03 11:21:14

# Updated on 2025-03-03 19:07:37

# Updated on 2025-03-06 20:12:38

# Updated on 2025-03-07 12:25:34

# Updated on 2025-03-08 17:19:24

# Updated on 2025-03-09 11:49:55

# Updated on 2025-03-09 17:45:01

# Updated on 2025-03-12 12:02:07

# Updated on 2025-03-13 12:07:39

# Updated on 2025-03-14 13:16:30

# Updated on 2025-03-15 10:49:12

# Updated on 2025-03-15 17:18:48

# Updated on 2025-03-16 18:06:53

# Updated on 2025-03-16 21:50:34

# Updated on 2025-03-17 10:40:39

# Updated on 2025-03-17 16:45:27

# Updated on 2025-03-19 08:31:58

# Updated on 2025-03-19 12:54:14

# Updated on 2025-03-19 18:09:56
