# FastAPI Structure

from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import SQLModel, create_engine, Session, select
from backend.models import TradeRequest, SnapshotRequest, ReturnRequest, SnapshotOut, PortfolioOut, StockOut, User, Portfolio, Snapshot
from backend.classes import Account, Stock
from backend.data_refresh import generate_returns, get_weights, generate_snapshot

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
app = FastAPI()
engine = create_engine("sqlite:///database.db")

account = Account()
init_db()

@app.get("/")
def root():
    return {"status": "Portfolio API is live"}

@app.post("/user/")
def create_user(username: str, session: Session = Depends(get_session)):
    user = User(username=username, created_at= datetime.now())
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

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

@app.get("/portfolio/simulate", response_model=PortfolioOut)
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

@app.get("/portfolio/{user_id}")
def get_user_portfolio(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    statement = select(Portfolio).where(Portfolio.user_id == user_id)
    results = session.exec(statement).all()

    return results
@app.post("/snapshot/preview", response_model=SnapshotOut)
def create_snapshot(req: SnapshotRequest):
    portfolio= {ticker: Stock(ticker, qty) for ticker, qty in req.portfolio.items()}
    snapshot= generate_snapshot(req.user_id, portfolio)
    snapshot["date"]= str(snapshot["date"])
    return snapshot

@app.get("/snapshot/store")
def store_snapshot(req: SnapshotRequest, session: Session = Depends(get_session)):
        snapshot_data = generate_snapshot(req.user_id, {
            ticker: Stock(ticker, quantity) for ticker, quantity in req.portfolio.items()
        })
        snapshot = Snapshot(
            user_id=req.user_id,
            date=datetime.strptime(snapshot_data["date"], "%Y-%m-%d").date(),
            prices=snapshot_data["prices"]
        )
        session.add(snapshot)
        session.commit()
        session.refresh(snapshot)
        return snapshot

@app.post("/returns")
def compute_returns(req: ReturnRequest):
    portfolio= {ticker: Stock(ticker, qty) for ticker, qty in req.portfolio.items()}
    weights= get_weights(portfolio)
    returns = generate_returns(req.snapshot_old, req.snapshot_new, weights)
    return {"returns": returns}

# def seed_users(engine):
#     """
#     Test function for db functionality
#     """
#     with Session(engine) as session:
#         existing = session.exec(select(User)).first()
#         if existing:
#             return
#
#         user1 = User(username="avery", created_at=datetime.now())
#         user2 = User(username="luke", created_at=datetime.now())
#         session.add_all([user1, user2])
#         session.commit()
#
# def seed_portfolio(engine):
#     """
#     Test function for db functionality.
#     """
#     with Session(engine) as session:
#         user = session.exec(select(User).where(User.username == "avery")).first()
#         if not user:
#             raise ValueError("User 'avery' not found")
#
#         existing = session.exec(select(Portfolio).where(Portfolio.user_id == user.id)).first()
#         if existing:
#             return
#
#         holdings = [
#             Portfolio(user_id=user.id, ticker="AAPL", quantity=3, created_at=datetime.now()),
#             Portfolio(user_id=user.id, ticker="MSFT", quantity=2, created_at=datetime.now()),
#             Portfolio(user_id=user.id, ticker="NVDA", quantity=1, created_at=datetime.now())
#         ]
#
#         session.add_all(holdings)
#         session.commit()
#
# seed_users(engine)
# seed_portfolio(engine)
