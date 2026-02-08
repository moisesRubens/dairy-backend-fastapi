from sqlalchemy import create_engine, Column, Boolean, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, UTC

db = create_engine("sqlite:///database/dairy_database.db")
Base = declarative_base()

class SalePoints(Base):
    __tablename__ = "sales_points"
    
    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String)
    email = Column("email", String)
    password = Column("password", String)
    
    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = password
        
class Order(Base):
    __tablename__ = "orders"
    
    id = Column("id", Integer, primary_key=True, autoincrement=True)
    status = Column("status", Boolean)
    total_value = Column("total_value", Float)
    description = Column("description", String, nullable=True)
    order_date = Column("order_date",  DateTime(timezone=True))
    items = relationship("ItemsOrder", back_populates="order", lazy="selectin")
    
    def __init__(self, description=None, status=False, order_datetime=None):
        self.description = description
        self.order_date = order_datetime or datetime.now(UTC)
        self.status = status

class Product(Base):
    __tablename__ = "products"
    
    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String)
    price = Column("price", Float)
    amount = Column("amount", Integer, nullable=True)
    kg = Column("kg", Float, nullable=True)
    liters = Column("liters", Float, nullable=True)
    
    def __init__(self, name, price, amount=None, kg=None, liters=None):
        self.name = name 
        self.price = price
        self.amount = amount
        self.kg = kg
        self.liters = liters
        
class ItemsOrder(Base):
    __tablename__ = "items_orders"
    
    order_id = Column("order_id", Integer, ForeignKey("orders.id"), primary_key=True)
    product_id = Column("product_id", Integer, ForeignKey("products.id"), primary_key=True)
    item_price = Column("item_price", Float)
    amount = Column("amount", Integer, nullable=True)
    kg = Column("kg", Float, nullable=True)
    liters = Column("liters", Float, nullable=True)
    order = relationship("Order", back_populates="items")
    
    def __init__(self, order_id: int, product_id: int, item_price, amount: int = None, kg: float = None, liters: float = None):
        self.order_id = order_id
        self.product_id = product_id
        self.amount = amount
        self.kg = kg
        self.liters = liters
        self.item_price = item_price

class OrderSalePoint(Base):
    __tablename__ = "order_sale_point"

    order_id = Column("order_id", Integer, ForeignKey("orders.id"), primary_key=True)
    sale_point_id = Column("sale_point_id", Integer, ForeignKey("sales_points.id"), primary_key=True)

    def __init__(self, order_id, sale_point_id):
        self.order_id = order_id
        self.sale_point_id = sale_point_id

Base.metadata.create_all(db)
