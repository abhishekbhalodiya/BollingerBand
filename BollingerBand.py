# BollingerBandsForexAlgorithm.py
# This is a LEAN algorithm that uses a Bollinger Bands strategy on a forex pair.
# It goes long when the current price falls below the lower Bollinger Band and
# exits the position when the price reverts above the middle band.
#
# Parameters:
#   pair      : (string) The forex currency pair to trade (e.g., "EURUSD"). Default is "EURUSD".
#   bb_period : (int)    The lookback period for the Bollinger Bands (default: 20).
#   bb_stddev : (float)  The standard deviation multiplier for the bands (default: 2.0).
#
# To optimize the strategy, you can expose additional variables like position sizing, stop-loss levels,
# take-profit percentages, and additional filters.
#
# Save this file in the LEAN Algorithms folder (e.g., Lean/Algorithm) before deploying.

from AlgorithmImports import *

class BollingerBandsForexAlgorithm(QCAlgorithm):

    def Initialize(self):
        # Set the backtesting start and end dates and initial cash
        self.SetStartDate(2022, 1, 1)
        self.SetEndDate(2022, 12, 31)
        self.SetCash(100000)
        
        # Retrieve user parameters for currency pair, Bollinger period, and standard deviation multiplier.
        # These can be set in the LEAN configuration file or passed as parameters.
        self.currencyPair = self.GetParameter("pair")
        if not self.currencyPair:
            self.currencyPair = "EURUSD"  # Default pair if no parameter is provided

        bb_period_param = self.GetParameter("bb_period")
        bb_stddev_param = self.GetParameter("bb_stddev")
        self.bb_period = int(bb_period_param) if bb_period_param is not None else 20
        self.bb_stddev = float(bb_stddev_param) if bb_stddev_param is not None else 2.0

        # Add the forex security to our algorithm. Here we use Oanda as an example market.
        forex_security = self.AddForex(self.currencyPair, Resolution.Minute, Market.Oanda)
        self.symbol = forex_security.Symbol

        # Create the Bollinger Bands indicator on the selected forex symbol.
        # The Bollinger Bands indicator uses a simple moving average by default.
        self.bb = self.BB(self.symbol, self.bb_period, self.bb_stddev, MovingAverageType.Simple, Resolution.Minute)

        # Set a warm-up period so that our Bollinger Bands are ready before trading begins.
        self.SetWarmUp(self.bb_period)

        # Schedule our TradeLogic function to run every minute during trading hours.
        self.Schedule.On(self.DateRules.EveryDay(self.symbol),
                         self.TimeRules.EveryMinute(self.symbol),
                         self.TradeLogic)

    def TradeLogic(self):
        # Do not execute trading logic until the warm-up period is complete.
        if self.IsWarmingUp:
            return

        # Get the current price of the forex pair.
        price = self.Securities[self.symbol].Price

        # Basic Bollinger Bands Strategy:
        # 1. If not currently invested and price falls below the lower Bollinger Band, enter a long position.
        if not self.Portfolio[self.symbol].Invested and price < self.bb.LowerBand.Current.Value:
            # Set holdings to 100% of the portfolio (this can be parameterized for risk management).
            self.SetHoldings(self.symbol, 1.0)
            self.Debug(f"Long Entry: Price {price:.5f} < LowerBand {self.bb.LowerBand.Current.Value:.5f}")

        # 2. If already invested and price rises above the middle band, exit the position.
        elif self.Portfolio[self.symbol].Invested and price > self.bb.MiddleBand.Current.Value:
            self.Liquidate(self.symbol)
            self.Debug(f"Exit: Price {price:.5f} > MiddleBand {self.bb.MiddleBand.Current.Value:.5f}")
