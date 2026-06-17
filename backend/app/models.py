from sqlalchemy import Column, String, Integer, Float, DateTime, Date
from .database import Base

class SaleOrder(Base):
    __tablename__ = "sale_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_date = Column(Date, index=True)
    order_no = Column(String(50), unique=True, index=True)
    product_code = Column(String(100))
    product_name = Column(String(500))
    brand = Column(String(100), index=True)
    channel = Column(String(100), index=True)   # 通路
    customer_code = Column(String(50))
    customer_name = Column(String(200))
    category = Column(String(100))              # 品類
    qty = Column(Integer)
    unit_price = Column(Float)
    discount = Column(Float)
    subtotal = Column(Float)
    year = Column(Integer, index=True)
    month = Column(Integer, index=True)

class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    purchase_date = Column(Date)
    product_code = Column(String(100))
    product_name = Column(String(500))
    brand = Column(String(100))
    qty = Column(Integer)
    unit_cost = Column(Float)
    total_cost = Column(Float)
    supplier = Column(String(200))
    year = Column(Integer, index=True)
    month = Column(Integer, index=True)

class SyncLog(Base):
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50))   # ecount / gsheets
    synced_at = Column(DateTime)
    records_updated = Column(Integer)
    status = Column(String(20))
    message = Column(String(500))
