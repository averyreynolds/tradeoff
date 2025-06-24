# FastAPI Structure

from fastapi import FastAPI, Body
from pydantic import BaseModel

app = FastAPI()

from backend.classes import Account
account = Account()

class TradeRequest(BaseModel):
    ticker: str
    quantity: int
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

@app.post("/snapshot")
def generate_snapshot(user_id:str, portfolio:dict= Body(...)):
    return {
        "message": f"Snapshot created for {user_id}",
        "portfolio": portfolio
    }

@app.get("/portfolio")
def view_portfolio():
    account.portfolio.refresh_prices()
    return {
        "cash": account.cash,
        "holdings": [
            {
                "ticker": stock.ticker,
                "shares": stock.quantity,
                "cost_basis": stock.cost_basis,
                "market_value": stock.market_value(),
                "stock": stock.percent_gain()
            }
            for stock in account.portfolio.holdings.values()
        ]
    }