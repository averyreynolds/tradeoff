from pydantic import BaseModel
from typing import Dict, Optional


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