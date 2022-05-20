from __future__ import absolute_import, division, print_function, unicode_literals
import datetime
import time
import itertools
import pandas as pd
from csv import writer

import backtrader as bt
from btplotting import BacktraderPlotting
from btplotting.schemes import Tradimo
from backtrader.indicators import MovAv


class macd_signal(bt.Indicator):
    # Uses MACD indicator to give crossover signals
    alias = ("MACDSIG",)
    params = (
        ("period_me1", 12),
        ("period_me2", 26),
        ("period_signal", 9),
        ("movav", MovAv.Exponential),
    )
    lines = (
        "mode",
        "sig",
    )
    plotinfo = dict(
        plot=True,
        subplot=True,
        plotname="",
        plotskip=False,
        plotabove=False,
        plotlinelabels=False,
        plotlinevalues=True,
        plotvaluetags=True,
        plotymargin=0.0,
        plotyhlines=[],
        plotyticks=[],
        plothlines=[],
        plotforce=False,
        plotmaster=None,
        plotylimited=True,
    )

    def __init__(self) -> None:
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.p.period_me1,
            period_me2=self.p.period_me2,
            period_signal=self.p.period_signal,
        )
        super(macd_signal, self).__init__()

    def next(self):
        # Set signal to 1 for buy and -1 to sell
        self.lines.mode[0] = 0.0
        self.lines.sig[0] = 0.0
        if self.macd.lines.macd[0] > 0.0:
            if self.macd.lines.macd[0] > self.macd.lines.signal[0]:
                self.lines.mode[0] = 1.0
        if self.lines.mode[0] == 1 and self.lines.mode[-1] == 0:
            self.lines.sig[0] = 1
        elif self.lines.mode[0] == 0 and self.lines.mode[-1] == 1:
            self.lines.sig[0] = -1


class main(bt.Strategy):

    params = dict(
        period_me1=12,
        period_me2=26,
        period_signal=9,
        size=0.99,
        save_exposure=True,
        calculate_commision=True,
    )

    def log_exposure(self, exposure, dt=None):
        # Log exposure into a csv file
        if self.p.save_exposure:
            dt = dt or self.data.datetime[0]
            dt = bt.num2date(dt)
            with open("exposure.csv", "a+", newline="") as write_obj:
                # Create a writer object from csv module
                csv_writer = writer(write_obj)
                # Add contents of list as last row in the csv file
                csv_writer.writerow([dt.strftime("%Y-%m-%d %H:%M:%S"), exposure])

    def log_comm(self, exposure, dt=None):
        # Log commisions in a csv file
        if self.p.calculate_commision:
            dt = dt or self.data.datetime[0]
            dt = bt.num2date(dt)
            with open("comm.csv", "a+", newline="") as write_obj:
                # Create a writer object from csv module
                csv_writer = writer(write_obj)
                # Add contents of list as last row in the csv file
                csv_writer.writerow([dt.strftime("%Y-%m-%d %H:%M:%S"), exposure])

    def __init__(self):
        # To control operation entries
        self.order = None
        self.exposure_df = pd.DataFrame
        # Indicators
        self.macd = macd_signal(
            self.datas[0],
            period_me1=self.p.period_me1,
            period_me2=self.p.period_me2,
            period_signal=self.p.period_signal,
        )

        # Keep track of oreders
        self.tradeid = itertools.cycle([0])

    def next(self):
        if self.order:
            return  # if an order is active, no new orders are allowed

        if self.datetime.time(ago=0) != datetime.time(
            12, 25, 00
        ):  # DO NOT buy at end of the day
            if self.macd.lines.sig > 0.0:  # buy signal
                self.curtradeid = next(self.tradeid)
                self.buy(tradeid=self.curtradeid)
            elif self.macd.lines.sig < 0.0:  # close long
                if self.position:
                    self.close(tradeid=self.curtradeid)
        else:
            if self.position:
                # self.log('CLOSE LONG , %.2f' % self.data.close[0])
                self.close(tradeid=self.curtradeid)

        if self.position:
            self.log_exposure(f"{self.p.size}")
        else:
            self.log_exposure("0.00")

    def notify_order(self, order):
        if order.status in [bt.Order.Submitted, bt.Order.Accepted]:
            return  # Await further notifications
        if order.status == order.Completed:
            self.log_comm(order.executed.comm, order.executed.dt)


def starter(
    data_name="DaraTestSet3",  # name of test set
    fromdate=datetime.datetime(2021, 7, 14),
    todate=datetime.datetime(2021, 9, 7),
):
    calculate_commision = (
        True  # Set true if you want to recalculate exposures. may take a few minutes
    )
    save_exposure = (
        True  # Set true if you want to recalculate exposures. may take a few minutes
    )
    if save_exposure:
        filename = "exposure.csv"
        f = open(filename, "w+")
        f.close()

    if calculate_commision:
        filename = "comm.csv"
        f = open(filename, "w+")
        f.close()

    # Keep a refrence to start time
    start = time.time()

    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    data = bt.feeds.GenericCSVData(
        dataname=f"./{data_name}.csv",
        fromdate=fromdate,
        todate=todate,
        dtformat=("%Y-%m-%d %H:%M:%S"),
        timeframe=bt.TimeFrame.Minutes,
        compression=5,
        datetime=9,
        high=3,
        low=4,
        open=2,
        close=5,
        volume=7,
        openinterest=-1,
    )
    cerebro.adddata(data, name="dara")
    # Set our desired cash
    cerebro.broker.setcash(1000000000.0)
    # use 99 percent of cash to buy the position, allocating 100 percent causes order rejection
    size = 0.99
    cerebro.addsizer(bt.sizers.AllInSizer, percents=size * 100)
    # set commission to 0.1 percent as a multiplier
    cerebro.broker.setcommission(commission=0.001)
    # Print out the starting conditions
    starting_value = cerebro.broker.getvalue()
    print("Starting Portfolio Value: %.2f" % starting_value)
    cerebro.addstrategy(
        main,
        period_me1=1,
        period_me2=25,
        period_signal=16,
        size=size,
        save_exposure=save_exposure,
        calculate_commision=calculate_commision,
    )

    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trade")
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
    thestrats = cerebro.run()

    # Print out the final result
    time_elapsed = time.time() - start
    print("Backtest finished in seconds: {}".format(time_elapsed))
    end_value = cerebro.broker.getvalue()
    profit = ((end_value - starting_value) / starting_value) * 100
    print(f"Final Portfolio Value: {end_value} Profit: {profit}")
    exposure_df = pd.read_csv("./exposure.csv")
    avg_exp = exposure_df[exposure_df.columns[1]].mean()
    print(f"Mean exposure: {avg_exp}")
    comm_df = pd.read_csv("./comm.csv")
    sum_comm = comm_df[comm_df.columns[1]].sum()
    print(f"Total commision: {sum_comm}")
    print(
        f"Total trades: {thestrats[0].analyzers.trade.get_analysis()['total']['closed']}"
    )
    print(
        f"Drawdown: {thestrats[0].analyzers.drawdown.get_analysis()['max']['drawdown']}"
    )

    # #Create final xls file
    final_result_file = pd.read_csv(f"./exposure.csv", index_col=False)
    mapping = {
        final_result_file.columns[0]: "Datetime",
        final_result_file.columns[1]: "Exposure",
    }
    final_result_file = final_result_file.rename(columns=mapping)
    final_result_file["Datetime"] = pd.to_datetime(
        final_result_file["Datetime"]
    ).dt.strftime("%Y-%m-%dT %H:%M:%SZ")
    final_result_file = final_result_file.set_index("Datetime")
    final_result_file.to_excel(f"{data_name}_results.xlsx")

    # ploting
    p = BacktraderPlotting(style="bar")
    cerebro.plot(p, scheme=Tradimo())


if __name__ == "__main__":
    starter(
        data_name="DaraTestSet3",
        fromdate=datetime.datetime(2021, 7, 14),
        todate=datetime.datetime(2021, 9, 7)
    )
