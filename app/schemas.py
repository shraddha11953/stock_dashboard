from pydantic import BaseModel
from datetime import date
from typing import List, Optional

class DayData(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    adj_close: float
    volume: float
    daily_return: Optional[float]
    ma_7: Optional[float]

    class Config:
        orm_mode = True

class Summary(BaseModel):
    symbol: str
    week52_high: float
    week52_low: float
    avg_close: float
