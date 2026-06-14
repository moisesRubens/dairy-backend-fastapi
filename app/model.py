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
    # Papel de acesso: "admin" (dono da fazenda) ou "vendedor" (ponto de venda).
    # Default "vendedor" para preservar o comportamento das contas existentes.
    role = Column("role", String(20), nullable=False, server_default=text("'vendedor'"))
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
    @property
    def sale_point_id(self):
        if self.order_sale_point and len(self.order_sale_point) > 0:
            return self.order_sale_point[0].sale_point_id
    
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
    outbound = relationship(
        "RetiradaProduto",
        back_populates="product"
    )
        
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
    @property
    def name(self):
        return self.product.name

class OrderSalePoint(Base):
    __tablename__ = "order_sale_point"

    order_id = Column("order_id", Integer, ForeignKey("orders.id", ondelete='CASCADE'), primary_key=True)
    sale_point_id = Column("sale_point_id", Integer, ForeignKey("sales_points.id", ondelete="CASCADE"), primary_key=True)
    order_date = Column("order_date", DateTime(timezone=True), default=lambda:datetime.now(tz=ZoneInfo("America/Sao_Paulo")), nullable=True)
    
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
    
    product = relationship(
        "Product",
        back_populates="outbound"
    )
        
    @property
    def set_remaining_quantity(self, remaining: None) -> float:
        self.remaining_quantity = self.taken_quantity - self.sold_quantity

    sale_point = relationship("SalePoints", back_populates="retiradas")


class StockRequest(Base):
    """Solicitação de reposição de estoque feita por um vendedor.

    Fluxo: vendedor cria (PENDING) -> admin aprova (APPROVED, aplica o estoque
    ao ponto e gera a retirada) ou recusa (REJECTED, com motivo). O vendedor
    pode cancelar a própria solicitação ainda pendente (CANCELLED).
    """
    __tablename__ = "stock_requests"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    requested_by_id = Column(Integer, ForeignKey("sales_points.id", ondelete="SET NULL"), nullable=True)
    target_point_id = Column(Integer, ForeignKey("sales_points.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Float, nullable=False)
    unidade = Column(String(10), nullable=False)  # amount | kg | liters
    status = Column(String(10), nullable=False, server_default=text("'PENDING'"))  # PENDING|APPROVED|REJECTED|CANCELLED
    reason = Column(String(255), nullable=True)  # motivo da recusa / observação do admin
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(tz=ZoneInfo("America/Sao_Paulo")))
    decided_at = Column(DateTime(timezone=True), nullable=True)
    decided_by_id = Column(Integer, ForeignKey("sales_points.id", ondelete="SET NULL"), nullable=True)
    applied_outbound_id = Column(Integer, ForeignKey("retiradas_produto.id", ondelete="SET NULL"), nullable=True)

    product = relationship("Product")
