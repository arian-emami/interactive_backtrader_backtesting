# interactive_backtrader_backtesting
Not so long ago I was tasked to create an interactive backtest report for an index fund at the Tehran stock exchange and this is the result. It performs a simple strategy based on a signal it generates from the MACD indicator. The total portfolio exposure and commissions paid are logged separately in two CSV files. Total portfolio exposure is also saved as an excel file for further analysis. At the end, a web based report is presented.\
This code was meant to be used as a boilerplate and the strategy itself is of no value.

![image of web_based report](https://github.com/arian-emami/interactive_backtrader_backtesting/raw/main/Screenshot.png?raw=true)
## Use guide
### Requirments:
install them all with:
```
pip install -r requirements.txt
```
or manually:
*   Python 3.7
*   openpyxl
*   Backtrader
*   git+https://github.com/happydasch/btplotting

### Run The backtest
Go to ending lines of backtest.py and change the settings as you wish:
```python
if __name__ == "__main__":
    starter(
        data_name="DaraTestSet3", # enter dataset name here
        fromdate=datetime.datetime(2021, 7, 14), # start day of backtest
        todate=datetime.datetime(2021, 9, 7) # end day of backtest + 1
    )
```
Keep in mind that end date must be one day later because of how python ranges work.\
When backtest is finshed you will be presented with the resault both in terminal and in a web page.

Feel free to ask me any questions.


