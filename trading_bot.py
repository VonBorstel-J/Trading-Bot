import backtrader as bt
import alpaca_backtrader_api
import datetime
import logging
import itertools

class TradingBot:
    def __init__(self, symbols, api_key, api_secret, base_url, start_date, end_date, live=False):
        self.symbols = symbols
        self.api = alpaca_backtrader_api.AlpacaStore(key_id=api_key, secret_key=api_secret, usePolygon=False)
        self.start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        self.live = live
        self.logger = logging.getLogger('TradingBot')
        self.logger.setLevel(logging.INFO)
        self.stop_flag = False

    def run(self):
        try:
            cerebro = bt.Cerebro(stdstats=False)

            if self.live:
                broker = self.api.getbroker()
            else:
                broker = bt.brokers.BackBroker(slip_perc=0.05)  # 5% slippage
            cerebro.setbroker(broker)

            # Add data for all symbols
            for symbol in self.symbols:
                if self.live:
                    data = self.api.getdata(symbol=symbol, historical=False, timeframe=bt.TimeFrame.Days)
                else:
                    data = self.api.getdata(symbol=symbol, historical=True, fromdate=self.start_date, todate=self.end_date, timeframe=bt.TimeFrame.Days)
                cerebro.adddata(data)

            cerebro.addstrategy(SmaCross, parent=self)
            cerebro.run()
            self.logger.info("Backtest finished successfully")
        except Exception as e:
            self.logger.error(f"An error occurred while running the backtest: {str(e)}")

    def stop(self):
        self.stop_flag = True


class SmaCross(bt.Strategy):
    params = dict(
        pfast=10,  # period for the fast moving average
        pslow=50,  # period for the slow moving average
        atrperiod=14,  # period for ATR
        stop_loss=2,  # stop loss is 2x ATR
        take_profit=3,  # take profit is 3x ATR
        risk_frac=0.02  # risk fraction per trade
    )

    def __init__(self, parent=None):
        self.parent = parent
        self.inds = dict()

        for i, d in enumerate(self.datas):
            self.inds[d] = dict()
            self.inds[d]['sma1'] = bt.indicators.SMA(d.close, period=self.p.pfast)
            self.inds[d]['sma2'] = bt.indicators.SMA(d.close, period=self.p.pslow)
            self.inds[d]['atr'] = bt.indicators.ATR(d, period=self.p.atrperiod)
            self.inds[d]['crossover'] = bt.indicators.CrossOver(self.inds[d]['sma1'], self.inds[d]['sma2'])

    def next(self):
        if self.parent and self.parent.stop_flag:
            for i, d in enumerate(self.datas):
                self.sell(data=d)  # Close any open position and stop the backtest
            return

        for i, d in enumerate(self.datas):
            if self.getposition(d).size:
                if self.inds[d]['crossover'] < 0:  # in the market & cross to the downside
                    self.close(data=d)  # close long position
            elif self.inds[d]['crossover'] > 0:  # not in the market and fast crosses slow to the upside
                cash = self.broker.getcash()
                value = self.broker.getvalue()
                size = min(cash / (d.close[0] * (1.0 + self.inds[d]['atr'][0])), self.p.risk_frac * value / (d.close[0] * self.inds[d]['atr'][0]))
                stop_price = d.close[0] - self.p.stop_loss * self.inds[d]['atr'][0]
                limit_price = d.close[0] + self.p.take_profit * self.inds[d]['atr'][0]
                self.buy(size=size, exectype=bt.Order.StopLimit, price=limit_price, plimit=stop_price, data=d)
