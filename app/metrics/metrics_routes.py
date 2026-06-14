from fastapi import APIRouter, Depends
from dependencies import make_session
from sales_points.sale_point_dependencies import require_admin
from metrics import metrics_service as svc

metrics_router = APIRouter(prefix="/admin/metrics", tags=["Metrics"])


@metrics_router.get("/summary")
async def summary(user = Depends(require_admin), session = Depends(make_session)):
    # Visão geral do dono: faturamento total/dia, pedidos, pendências, etc.
    return svc.get_summary_service(session)


@metrics_router.get("/revenue/by-point")
async def revenue_by_point(user = Depends(require_admin), session = Depends(make_session)):
    # Ranking de faturamento por ponto de venda.
    return svc.get_revenue_by_point_service(session)
