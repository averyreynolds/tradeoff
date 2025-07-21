# FastAPI Structure

from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, create_engine, Session, select, and_
from backend.models import TradeRequest, SnapshotRequest, ReturnRequest, SignupRequest, SnapshotOut, PortfolioOut, StockOut, User, PortfolioDB, Snapshot
from backend.classes import Account, Stock
from backend.data_refresh import generate_returns, get_weights, generate_snapshot

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

engine = create_engine("sqlite:///database.db")
account = Account()

app = FastAPI()
init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],        # NEED TO CONFINE LATER
    allow_credentials=True,
    allow_methods=["*"],        # Allow backend to receive headers
    allow_headers=["*"]         # Will need for authentication
)
@app.get("/")
def root():
    return {"status": "Portfolio API is live"}

@app.post("/signup")
def signup(request: SignupRequest, session: Session = Depends(get_session)):
    new_user = User(username=request.email, created_at=datetime.now(), cash=10000.0)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return {"user_id": new_user.id, "cash": new_user.cash}

# --- Buy Stock ---
@app.post("/buy")
def buy_stock(trade: TradeRequest, session: Session = Depends(get_session)):
    user = session.get(User, trade.user_id)

    stock = Stock(ticker=trade.ticker.upper(), quantity=trade.quantity)
    stock.refresh_price()
    total_cost = stock.current_price * trade.quantity

    if total_cost > user.cash:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    existing = session.exec(
        select(PortfolioDB).where(
            and_(
                PortfolioDB.user_id == trade.user_id,
                PortfolioDB.ticker == stock.ticker
            )
        )
    ).first()

    if existing:
        total_quantity = existing.quantity + stock.quantity
        total_cost_basis = (existing.purchase_price * existing.quantity) + total_cost
        existing.quantity = total_quantity
        existing.purchase_price = total_cost_basis / total_quantity
        session.add(existing)
    else:
        new_entry = PortfolioDB(
            user_id=trade.user_id,
            ticker=stock.ticker,
            quantity=stock.quantity,
            purchase_price=stock.current_price
        )
        session.add(new_entry)

    user.cash -= total_cost
    session.add(user)

    session.commit()
    return {
        "message": f"Bought {trade.quantity} shares of {stock.ticker} at {stock.current_price:.2f}",
        "remaining_cash": user.cash
    }

# --- Sell Stock ---
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

# --- View User Portfolio ---
@app.get("/portfolio/{user_id}", response_model=PortfolioOut)
def get_user_portfolio(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    holdings = session.exec(
        select(PortfolioDB).where(PortfolioDB.user_id == user_id)
    ).all()

    portfolio_items = []
    for item in holdings:
        stock = Stock(item.ticker, item.quantity)
        stock.refresh_price()
        mv = stock.market_value()
        portfolio_items.append(
            StockOut(
                ticker=item.ticker,
                quantity=item.quantity,
                cost_basis=item.purchase_price * item.quantity,
                market_value=mv,
                percent_gain=((mv-(item.purchase_price * item.quantity))/(item.purchase_price * item.quantity)) * 100 if item.purchase_price else 0
            )
        )
    return PortfolioOut(
        cash=user.cash,
        holdings=portfolio_items
    )

@app.post("/snapshot/preview", response_model=SnapshotOut)
def create_snapshot(req: SnapshotRequest):
    portfolio= {ticker: Stock(ticker, qty) for ticker, qty in req.portfolio.items()}
    snapshot= generate_snapshot(req.user_id, portfolio)
    snapshot["date"]= str(snapshot["date"])
    return snapshot

@app.post("/snapshot/store")
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
