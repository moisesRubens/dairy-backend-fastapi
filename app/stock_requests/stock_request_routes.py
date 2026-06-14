from fastapi import APIRouter, Depends
from dependencies import make_session
from sales_points.sale_point_dependencies import validate_token, require_admin
from stock_requests.stock_request_schema import StockRequestCreateDTO, StockRequestRejectDTO
from stock_requests import stock_request_service as svc

stock_request_router = APIRouter(prefix="/stock-requests", tags=["StockRequest"])


@stock_request_router.post("/", status_code=201)
async def create(data: StockRequestCreateDTO, user = Depends(validate_token), session = Depends(make_session)):
    # Vendedor solicita reposição para o PRÓPRIO ponto (target = id do usuário).
    return svc.create_stock_request_service(session, user["sale_point_id"], data)


@stock_request_router.get("/")
async def index(user = Depends(validate_token), session = Depends(make_session)):
    # Admin vê todas; vendedor vê só as do próprio ponto.
    return svc.list_stock_requests_service(session, user)


@stock_request_router.get("/{request_id}")
async def show(request_id: int, user = Depends(validate_token), session = Depends(make_session)):
    return svc.get_stock_request_service(session, user, request_id)


@stock_request_router.post("/{request_id}/approve")
async def approve(request_id: int, user = Depends(require_admin), session = Depends(make_session)):
    return svc.approve_stock_request_service(session, user["sale_point_id"], request_id)


@stock_request_router.post("/{request_id}/reject")
async def reject(request_id: int, body: StockRequestRejectDTO, user = Depends(require_admin), session = Depends(make_session)):
    return svc.reject_stock_request_service(session, user["sale_point_id"], request_id, body.reason)


@stock_request_router.post("/{request_id}/cancel")
async def cancel(request_id: int, user = Depends(validate_token), session = Depends(make_session)):
    return svc.cancel_stock_request_service(session, user, request_id)
