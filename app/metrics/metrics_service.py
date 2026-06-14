from datetime import date
from sqlalchemy import func
from model import Order, OrderSalePoint, SalePoints, Product, StockRequest


def get_summary_service(session):
    """Números-chave para o card de visão geral do admin."""
    total_revenue = session.query(func.coalesce(func.sum(Order.total_value), 0.0)).scalar() or 0.0
    revenue_today = session.query(func.coalesce(func.sum(Order.total_value), 0.0)) \
        .filter(func.date(Order.order_date) == date.today()).scalar() or 0.0
    orders_count = session.query(func.count(Order.id)).scalar() or 0
    vendors_count = session.query(func.count(SalePoints.id)).filter(SalePoints.role == "vendedor").scalar() or 0
    products_count = session.query(func.count(Product.id)).scalar() or 0
    pending_requests = session.query(func.count(StockRequest.id)).filter(StockRequest.status == "PENDING").scalar() or 0

    return {
        "total_revenue": round(float(total_revenue), 2),
        "revenue_today": round(float(revenue_today), 2),
        "orders_count": int(orders_count),
        "vendors_count": int(vendors_count),
        "products_count": int(products_count),
        "pending_requests": int(pending_requests),
    }


def get_revenue_by_point_service(session):
    """Ranking de faturamento por ponto de venda (maior para menor)."""
    rows = session.query(
        OrderSalePoint.sale_point_id,
        SalePoints.name,
        func.coalesce(func.sum(Order.total_value), 0.0),
        func.count(Order.id),
    ).join(Order, Order.id == OrderSalePoint.order_id) \
     .join(SalePoints, SalePoints.id == OrderSalePoint.sale_point_id) \
     .group_by(OrderSalePoint.sale_point_id, SalePoints.name) \
     .order_by(func.sum(Order.total_value).desc()).all()

    return [
        {
            "sale_point_id": sp_id,
            "name": name,
            "revenue": round(float(revenue or 0.0), 2),
            "orders_count": int(orders or 0),
        }
        for sp_id, name, revenue, orders in rows
    ]
