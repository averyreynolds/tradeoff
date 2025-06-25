from pydantic import BaseModel
from typing import Dict, Optional
from sqlmodel import SQLModel, Field, JSON, Column
from datetime import datetime, date


# Inputs
class TradeRequest(BaseModel):
    ticker:str
    quantity:int

class SnapshotRequest(BaseModel):
    user_id:str
    portfolio: Dict[str, int]

class ReturnRequest(BaseModel):
    snapshot_old:dict
    snapshot_new:dict
    portfolio: Dict[str, int]

#Outputs
class StockOut(BaseModel):
    ticker:str
    quantity:int
    cost_basis:float
    market_value:float
    percent_gain: Optional[float]

class PortfolioOut(BaseModel):
    cash:float
    holdings: list[StockOut]

class SnapshotOut(BaseModel):
    user_id:str
    date:str
    prices: Dict[str, float]

class ReturnOut(BaseModel):
    returns: Dict[str, float]

# DB Models
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    created_at: datetime

class Portfolio(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    ticker: str
    quantity: float
    created_at: datetime

class Snapshot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    date: date
    prices: Dict[str, float] = Field(sa_column=Column(JSON))
