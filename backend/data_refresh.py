def generate_snapshot(user_id:str, portfolio:dict) -> dict:
    """
    Given a user ID and the user's portfolio,
    return a dictionary with the user ID, date of snapshot, and prices in portfolio

    Parameters:
        - user_id: "avery123"
        - portfolio: { "AAPL": Stock("AAPL", 2) }

    Returns:
        - {
            user_id: "avery123",
            date: "06-24-25",
            prices: { "AAPL": 225.79 }
        }
    """
    import yfinance as yf
    import datetime

    tickers = list(portfolio.keys())
    data = yf.download(tickers,period="1d")["Adj Close"].iloc[-1]

    return {
        "user_id": user_id,
        "date": datetime.date.today(),
        "prices": {ticker: round(data[ticker]) for ticker in tickers}
    }

def get_weights(portfolio:dict) -> dict:
    total_value = sum(stock.market_value() for stock in portfolio.values())
    return {
        ticker: stock.market_value() / total_value
        for ticker, stock in portfolio.items()
    }

def generate_returns(snapshot_old:dict, snapshot_new:dict, weights:dict) -> dict:
    """
    Given an old and new snapshot, and a portfolio of weight allocations,
    return individual ticker % returns and the total weighted return

    Parameters:
        - snapshot_old/snapshot_new: { 'prices': { 'AAPL': 180.0, 'MSFT': 320.0 } }
        - portfolio: { 'AAPL': 0.6, 'MSFT': 0.4 }

    Returns:
        - { 'AAPL': 5.56, 'MSFT': 6.25, 'total_return': 5.91 }
    """
    prices_old = snapshot_old["prices"]
    prices_new = snapshot_new["prices"]

    returns = {}
    total_return = 0.0

    for ticker, weight in weights.items():
        if ticker not in prices_old or ticker not in prices_new:
            raise ValueError(f"Missing price data for ticker: {ticker}")

        old_price = prices_old[ticker]
        new_price = prices_new[ticker]

        if old_price == 0:
            raise ValueError(f"Old price for {ticker} is zero. Results in zero division.")

        percent_change = ((new_price - old_price) / old_price) * 100
        returns[ticker] = round(percent_change, 2)
        total_return += weight * percent_change

    returns["Total Return"] = round(total_return, 2)
    return returns
