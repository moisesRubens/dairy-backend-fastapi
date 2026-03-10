from sqlalchemy import create_engine, Column, Boolean, Integer, Float, String, DateTime, ForeignKey, text
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
from zoneinfo import ZoneInfo

db = create_engine("sqlite:///database/dairy_database.db")
Base = declarative_base()

class SalePoints(Base):
    __tablename__ = "sales_points"
    
    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String(100))
    email = Column("email", String(200), nullable=True, unique=False)
    password = Column("password", String(200))
    order_sale_point = relationship(
        "OrderSalePoint",
        cascade="all, delete-orphan",
        back_populates="sale_point"
    )
    retiradas = relationship("RetiradaProduto", back_populates="sale_point", cascade="all, delete-orphan")
        
class Order(Base):
    __tablename__ = "orders"
    
    id = Column("id", Integer, primary_key=True, autoincrement=True)
    status = Column("status", Boolean, server_default=text('TRUE'), nullable=False)
    total_value = Column("total_value", Float, nullable=False)
    description = Column("description", String(200), nullable=True)
    order_date = Column("order_date",  DateTime(timezone=True), default=lambda:datetime.now(tz=ZoneInfo("America/Sao_Paulo")), nullable=False)
    item_order = relationship(
        "ItemsOrder",
        back_populates="order",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin"
    )
    order_sale_point = relationship(
        "OrderSalePoint",
        back_populates="order",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin"
    )
    

class Product(Base):
    __tablename__ = "products"
    
    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String(100), nullable=False, unique=True)
    price = Column("price", Float, nullable=True)
    amount = Column("amount", Integer, nullable=True)
    kg = Column("kg", Float, nullable=True)
    liters = Column("liters", Float, nullable=True)
    item_order = relationship(
        "ItemsOrder",
        back_populates="product",
        passive_deletes=True
    )
    retiradas = relationship("RetiradaProduto", back_populates="product", cascade="all, delete-orphan")
        
class ItemsOrder(Base):
    __tablename__ = "item_order"
    
    order_id = Column("order_id", Integer, ForeignKey("orders.id", ondelete="CASCADE"), primary_key=True)
    product_id = Column("product_id", Integer, ForeignKey("products.id", ondelete="CASCADE"), primary_key=True)
    item_price = Column("item_price", Float, nullable=False)
    amount = Column("amount", Integer, nullable=True)
    kg = Column("kg", Float, nullable=True)
    liters = Column("liters", Float, nullable=True)
    order = relationship(
        "Order",
        back_populates="item_order"
    )
    product = relationship(
        "Product",
        back_populates="item_order"
    )
    

class OrderSalePoint(Base):
    __tablename__ = "order_sale_point"

    order_id = Column("order_id", Integer, ForeignKey("orders.id", ondelete='CASCADE'), primary_key=True)
    sale_point_id = Column("sale_point_id", Integer, ForeignKey("sales_points.id", ondelete="CASCADE"), primary_key=True)
    order = relationship(
        "Order",
        back_populates="order_sale_point"
    )
    sale_point = relationship(
        "SalePoints",
        back_populates="order_sale_point"
    )

class Token(Base):
    __tablename__ = 'tokens'

    id = Column(String, primary_key=True)

class RetiradaProduto(Base):
    __tablename__ = "retiradas_produto"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sale_point_id = Column(Integer, ForeignKey("sales_points.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    taken_quantity = Column(Float, nullable=False)
    unidade = Column(String(10), nullable=False)  
    observacao = Column(String(200), nullable=True)
    data = Column(DateTime, default=lambda: datetime.now(ZoneInfo("America/Sao_Paulo")))
    sold_quantity = Column(Float, nullable=False, default=0)
    total_value = Column(Float, nullable=False, default=0)
    status = Column(Boolean, nullable=False, server_default=text('TRUE'))
    remaining_quantity = Column(Float, nullable=True, default=0)
    
    @property
    def set_remaining_quantity(self, remaining: None) -> float:
        self.remaining_quantity = self.taken_quantity - self.sold_quantity

    sale_point = relationship("SalePoints", back_populates="retiradas")
    product = relationship("Product", back_populates="retiradas")
