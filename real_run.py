import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import time
import datetime
import os

# Configuration
SYMBOL = "BA"  # Stock symbol to monitor
SHORT_TERM_WINDOW = 5  # Short-term EMA window
LONG_TERM_WINDOW = 20  # Long-term EMA window
CHECK_INTERVAL = 3600  # Check for new signals every hour (in seconds)
INITIAL_BALANCE = 100  # Starting balance for tracking purposes

# File to store trade log
TRADE_LOG_FILE = "trade212_signals.csv"

class Trade212Monitor:
    def __init__(self, symbol, short_window, long_window):
        self.symbol = symbol
        self.short_window = short_window
        self.long_window = long_window
        self.position = False  # Whether we currently hold the stock
        self.last_price = 0
        self.shares = 0
        self.balance = INITIAL_BALANCE
        self.trade_log = []
        
        # Load previous trade log if exists
        self.load_trade_log()
        
        # Get current position from the last trade
        if len(self.trade_log) > 0:
            last_trade = self.trade_log[-1]
            if last_trade['Action'] in ['BUY', 'FINAL BUY']:
                self.position = True
                self.shares = last_trade['Shares']
                self.balance = 0
            else:
                self.position = False
                self.shares = 0
                self.balance = last_trade['USD Balance']
    
    def load_trade_log(self):
        """Load existing trade log if available"""
        if os.path.exists(TRADE_LOG_FILE):
            try:
                df = pd.read_csv(TRADE_LOG_FILE)
                df['Date'] = pd.to_datetime(df['Date'])
                self.trade_log = df.to_dict('records')
                print(f"Loaded {len(self.trade_log)} previous trades from log")
            except Exception as e:
                print(f"Error loading trade log: {e}")
                self.trade_log = []
        else:
            self.trade_log = []
    
    def save_trade_log(self):
        """Save trade log to CSV file"""
        pd.DataFrame(self.trade_log).to_csv(TRADE_LOG_FILE, index=False)
        
    def get_latest_data(self):
        """Get the latest stock data with enough history for EMAs"""
        # We need enough historical data to calculate EMAs
        # Get data for twice the long window to ensure enough history
        lookback_period = f"{self.long_window * 3}d"
        
        try:
            stock = yf.Ticker(self.symbol)
            data = stock.history(period=lookback_period)
            
            # Rename columns to match our strategy
            data = data.rename(columns={
                'Close': 'close',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Volume': 'volume'
            })
            
            return data
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None
    
    def calculate_emas(self, data):
        """Calculate EMAs for the data"""
        short_ema = data['close'].ewm(span=self.short_window, adjust=False).mean()
        long_ema = data['close'].ewm(span=self.long_window, adjust=False).mean()
        return short_ema, long_ema
    
    def check_for_signals(self):
        """Check for new trading signals"""
        data = self.get_latest_data()
        if data is None:
            print("Could not get market data. Will try again later.")
            return
        
        # Get the latest price
        self.last_price = data['close'].iloc[-1]
        
        # Calculate EMAs
        short_ema, long_ema = self.calculate_emas(data)
        
        # Check for crossovers (using the last two data points)
        current_short = short_ema.iloc[-1]
        current_long = long_ema.iloc[-1]
        prev_short = short_ema.iloc[-2]
        prev_long = long_ema.iloc[-2]
        
        # Get current time
        current_time = datetime.datetime.now()
        
        # Check for buy signal (short EMA crosses above long EMA)
        if current_short > current_long and prev_short <= prev_long:
            if not self.position:
                # Generate buy signal
                self.shares = self.balance / self.last_price
                self.balance = 0
                self.position = True
                
                trade = {
                    'Date': current_time,
                    'Action': 'BUY',
                    'Price': self.last_price,
                    'Shares': self.shares,
                    'USD Balance': self.balance
                }
                self.trade_log.append(trade)
                self.save_trade_log()
                
                print(f"\n🟢 BUY SIGNAL at {self.last_price:.2f} on {current_time}")
                print(f"    Buy {self.shares:.6f} shares of {self.symbol}")
                print(f"    Open Trade212 and execute this trade manually!")
                self.display_signal_details(short_ema, long_ema)
        
        # Check for sell signal (short EMA crosses below long EMA)
        elif current_short < current_long and prev_short >= prev_long:
            if self.position:
                # Generate sell signal
                self.balance = self.shares * self.last_price
                self.shares = 0
                self.position = False
                
                trade = {
                    'Date': current_time,
                    'Action': 'SELL',
                    'Price': self.last_price,
                    'Shares': self.shares,
                    'USD Balance': self.balance
                }
                self.trade_log.append(trade)
                self.save_trade_log()
                
                print(f"\n🔴 SELL SIGNAL at {self.last_price:.2f} on {current_time}")
                print(f"    Sell all {self.symbol} shares")
                print(f"    Open Trade212 and execute this trade manually!")
                self.display_signal_details(short_ema, long_ema)
        
        # No new signal, just update status
        else:
            self.display_status(short_ema, long_ema)
    
    def display_signal_details(self, short_ema, long_ema):
        """Display detailed information about a trading signal"""
        print(f"\nSignal Details:")
        print(f"    Short EMA ({self.short_window}): {short_ema.iloc[-1]:.2f}")
        print(f"    Long EMA ({self.long_window}): {long_ema.iloc[-1]:.2f}")
        print(f"    Current Position: {'HOLDING' if self.position else 'CASH'}")
        print(f"    Current Balence : ${self.balance:.2f}")
        
        if self.position:
            current_value = self.shares * self.last_price
            print(f"    Current Value: ${current_value:.2f}")
        else:
            print(f"    Cash Balance: ${self.balance:.2f}")
    
    def display_status(self, short_ema, long_ema):
        """Display current status information"""
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\r[{current_time}] {self.symbol}: ${self.last_price:.2f} | Short EMA: {short_ema.iloc[-1]:.2f} | Long EMA: {long_ema.iloc[-1]:.2f} | {'HOLDING' if self.position else 'CASH'} | Current Balence: Current Balence : ${self.balance:.2f}")
    
    def calculate_performance(self):
        """Calculate and display performance metrics"""
        if len(self.trade_log) > 0:
            # Calculate current value
            if self.position:
                current_value = self.shares * self.last_price
            else:
                current_value = self.balance
                
            initial_value = INITIAL_BALANCE
            profit = current_value - initial_value
            roi = (profit / initial_value) * 100
            
            print("\n\nPerformance Summary:")
            print(f"Initial Balance: ${initial_value:.2f}")
            print(f"Current Value: ${current_value:.2f}")
            print(f"Profit: ${profit:.2f}")
            print(f"ROI: {roi:.2f}%")
            
            # Count trades
            buys = sum(1 for trade in self.trade_log if trade['Action'] == 'BUY')
            sells = sum(1 for trade in self.trade_log if trade['Action'] == 'SELL')
            print(f"Total Trades: {buys + sells} (Buys: {buys}, Sells: {sells})")
    
    def plot_current_state(self):
        """Plot the current state of the market with EMAs"""
        data = self.get_latest_data()
        if data is None:
            return
            
        # Calculate EMAs for plotting
        short_ema, long_ema = self.calculate_emas(data)
        
        # Plot the last 60 days of data
        plot_data = data.tail(60).copy()
        plot_short_ema = short_ema.tail(60)
        plot_long_ema = long_ema.tail(60)
        
        plt.figure(figsize=(14, 7))
        plt.plot(plot_data.index, plot_data['close'], label='Price', color='blue')
        plt.plot(plot_data.index, plot_short_ema, label=f'EMA {self.short_window}', color='red')
        plt.plot(plot_data.index, plot_long_ema, label=f'EMA {self.long_window}', color='green')
        
        # Plot buy and sell signals if available
        trade_df = pd.DataFrame(self.trade_log)
        if not trade_df.empty:
            trade_df['Date'] = pd.to_datetime(trade_df['Date'])
            recent_trades = trade_df[trade_df['Date'] >= plot_data.index[0]]
            
            if not recent_trades.empty:
                buys = recent_trades[recent_trades['Action'] == 'BUY']
                plt.scatter(buys['Date'], buys['Price'], marker='^', color='green', label='Buy Signal', alpha=1, s=100)
                
                sells = recent_trades[recent_trades['Action'] == 'SELL']
                plt.scatter(sells['Date'], sells['Price'], marker='v', color='red', label='Sell Signal', alpha=1, s=100)
        
        plt.xlabel('Date')
        plt.ylabel('Price (USD)')
        plt.title(f"{self.symbol} EMA Crossover Strategy - Live Monitor")
        plt.legend()
        plt.grid()
        plt.savefig('current_market_state.png')
        plt.close()
        print(f"\nCurrent market chart saved as 'current_market_state.png'")

def main():
    print(f"\n{'='*50}")
    print(f"🚀 Trade212 Live Trading Monitor for {SYMBOL}")
    print(f"{'='*50}")
    print(f"Strategy: EMA Crossover ({SHORT_TERM_WINDOW}/{LONG_TERM_WINDOW})")
    print(f"Checking for signals every {CHECK_INTERVAL/60:.1f} minutes")
    print(f"{'='*50}\n")
    
    monitor = Trade212Monitor(SYMBOL, SHORT_TERM_WINDOW, LONG_TERM_WINDOW)
    
    try:
        while True:
            monitor.check_for_signals()
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("\n\nStopping monitor. Final status:")
        monitor.calculate_performance()
        monitor.plot_current_state()
        print("\nMonitor stopped. Saved trade log.")

if __name__ == "__main__":
    main()