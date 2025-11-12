from sqlalchemy import Column, Integer, String, Float, Date
from sqlalchemy import UniqueConstraint
from app.db import Base

class Stock(Base):
    __tablename__ = "stock_daily"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    date = Column(Date, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    adj_close = Column(Float)
    volume = Column(Float)
    daily_return = Column(Float)
    ma_7 = Column(Float)
    
    __table_args__ = (UniqueConstraint("symbol", "date", name="uix_symbol_date"),)
