# FastAPI Structure

from fastapi import FastAPI
from backend.models import TradeRequest, SnapshotRequest, ReturnRequest, SnapshotOut, PortfolioOut, StockOut
from backend.classes import Account, Stock
from backend.data_refresh import generate_returns, get_weights, generate_snapshot

app = FastAPI()


account = Account()

@app.get("/")
def root():
    return {"status": "Portfolio API is live"}

@app.post("/buy")
def buy_stock(trade: TradeRequest):
    try:
        account.buy_stock(trade.ticker, trade.quantity)
        return {"message": f"Bought {trade.quantity} shares of {trade.ticker.upper()}"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/sell")
def sell_stock(trade: TradeRequest):
    try:
        account.sell_stock(trade.ticker, trade.quantity)
        return {"message": f"Sold {trade.quantity} shares of {trade.ticker.upper()}"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/portfolio", response_model=PortfolioOut)
def view_portfolio():
    account.portfolio.refresh_prices()
    return PortfolioOut(
        cash= account.cash,
        holdings= [
            StockOut(
                ticker= stock.ticker,
                quantity= stock.quantity,
                cost_basis= stock.cost_basis,
                market_value= stock.market_value(),
                percent_gain= stock.percent_gain()
            )
            for stock in account.portfolio.holdings.values()
        ]
    )

@app.post("/snapshot", response_model=SnapshotOut)
def create_snapshot(req: SnapshotRequest):
    portfolio= {ticker: Stock(ticker, qty) for ticker, qty in req.portfolio.items()}
    snapshot= generate_snapshot(req.user_id, portfolio)
    snapshot["date"]= str(snapshot["date"])
    return snapshot

@app.post("/returns")
def compute_returns(req: ReturnRequest):
    portfolio= {ticker: Stock(ticker, qty) for ticker, qty in req.portfolio.items()}
    weights= get_weights(portfolio)
    returns = generate_returns(req.snapshot_old, req.snapshot_new, weights)
    return {"returns": returns}