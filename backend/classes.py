# Data Structures for Portfolios
import yfinance as yf

class Stock:
    def __init__(self, ticker, quantity):
        self.ticker = ticker.upper()
        self.quantity = quantity
        self.purchase_price = self.get_current_price()
        self.cost_basis = self.purchase_price * self.quantity if self.purchase_price is not None else 0
        self.current_price = self.purchase_price

    def get_current_price(self):
        stock = yf.Ticker(self.ticker)
        try:
            return stock.fast_info["lastPrice"]
        except Exception:
            return None #when ticker DNE

    def market_value(self):
        current_price = self.get_current_price()
        return current_price * self.quantity if current_price else 0

    def refresh_price(self):
        price = self.get_current_price()
        if price:
            self.current_price = price

    def percent_gain(self):
        mv = self.market_value()
        return ((mv - self.cost_basis) / self.cost_basis) * 100 if self.cost_basis > 0 else 0

    def __repr__(self):
        cost_str = f"{self.cost_basis:.2f}" if self.cost_basis else "N/A"
        price_str = f"{self.market_value():.2f}" if self.market_value else "N/A"
        percent_str = f"{self.percent_gain():.2f}"
        return f"{self.ticker} | {self.quantity} | ${cost_str} | ${price_str} | {percent_str}%\n"

class Portfolio:
    def __init__(self):
        self.holdings = {}  #key: ticker, value: Stock

    def add_stock(self, ticker, quantity):
        ticker = ticker.upper()
        if ticker in self.holdings:
            stock = self.holdings[ticker]
            stock.quantity += quantity
            stock.cost_basis += quantity * stock.get_current_price()
        else:
            self.holdings[ticker] = Stock(ticker, quantity)

    def get_total_value(self):
        value = 0
        for ticker in self.holdings:
            value += self.holdings[ticker].market_value()
        return value

    def refresh_prices(self):
        for stock in self.holdings.values():
            stock.refresh_price()

    def print_info(self):
        # print("Ticker | Shares | Market Price | Total Value")
        for stock in self.holdings.values():
            print(f"{stock}", end="")
        print(f"\nTotal Value: ${self.get_total_value():.2f}\n")

class Account:
    def __init__(self, budget = 10000):
        self.portfolio = Portfolio()
        self.cash = budget

    def print_info(self):
        print(f"\nCurrent Balance: {self.cash:.2f}\n")
        self.portfolio.print_info()

    def buy_stock(self, ticker, quantity):
        ticker = ticker.upper()
        stock_price = Stock(ticker, 0).get_current_price()
        cost = stock_price * quantity
        if cost > self.cash:
            raise Exception("Cannot exceed budget!")
        self.portfolio.add_stock(ticker, quantity)
        self.cash -= cost

    def sell_stock(self, ticker, quantity):
        ticker = ticker.upper()
        if ticker in self.portfolio.holdings:
            stock = self.portfolio.holdings[ticker]
            if stock.quantity < quantity:
                raise Exception("Not enough shares to sell.")

            selling_price = stock.get_current_price()
            profit = selling_price * quantity
            self.cash += profit

            stock.cost_basis *= (stock.quantity - quantity) / stock.quantity
            stock.quantity -= quantity

            if stock.quantity == 0:
                del self.portfolio.holdings[ticker]
        else:
            raise Exception("No such stock found.")
