from datetime import datetime, date
from zoneinfo import ZoneInfo
from sqlalchemy import func
from fastapi import HTTPException
from model import StockRequest, Product, RetiradaProduto
from stock_requests.stock_request_schema import StockRequestCreateDTO, StockRequestResponseDTO

VALID_UNITS = {"amount", "kg", "liters"}

PENDING = "PENDING"
APPROVED = "APPROVED"
REJECTED = "REJECTED"
CANCELLED = "CANCELLED"


def _now():
    return datetime.now(tz=ZoneInfo("America/Sao_Paulo"))


def _to_response(req: StockRequest) -> StockRequestResponseDTO:
    return StockRequestResponseDTO(
        id=req.id,
        requested_by_id=req.requested_by_id,
        target_point_id=req.target_point_id,
        product_id=req.product_id,
        product_name=req.product.name if req.product else None,
        quantity=req.quantity,
        unidade=req.unidade,
        status=req.status,
        reason=req.reason,
        created_at=req.created_at,
        decided_at=req.decided_at,
        decided_by_id=req.decided_by_id,
        applied_outbound_id=req.applied_outbound_id,
    )


def create_stock_request_service(session, requester_id: int, data: StockRequestCreateDTO):
    if data.unidade not in VALID_UNITS:
        raise HTTPException(400, "unidade inválida (use amount, kg ou liters)")
    if data.quantity <= 0:
        raise HTTPException(400, "quantidade deve ser positiva")
    product = session.get(Product, data.product_id)
    if not product:
        raise HTTPException(404, "produto não encontrado")

    req = StockRequest(
        requested_by_id=requester_id,
        target_point_id=requester_id,  # vendedor solicita para o próprio ponto
        product_id=data.product_id,
        quantity=data.quantity,
        unidade=data.unidade,
        status=PENDING,
        created_at=_now(),
    )
    session.add(req)
    session.commit()
    session.refresh(req)
    return _to_response(req)


def list_stock_requests_service(session, user):
    query = session.query(StockRequest)
    if user.get("role") != "admin":
        # vendedor só vê as solicitações do próprio ponto
        query = query.filter(StockRequest.target_point_id == user.get("sale_point_id"))
    requests = query.order_by(StockRequest.created_at.desc()).all()
    return [_to_response(r) for r in requests]


def get_stock_request_service(session, user, request_id: int):
    req = session.get(StockRequest, request_id)
    if not req:
        raise HTTPException(404, "solicitação não encontrada")
    if user.get("role") != "admin" and req.target_point_id != user.get("sale_point_id"):
        raise HTTPException(403, "acesso negado")
    return _to_response(req)


def approve_stock_request_service(session, admin_id: int, request_id: int):
    """Aprova de forma ATÔMICA: revalida o estoque central, debita o produto,
    cria a retirada para o ponto e marca a solicitação como APPROVED. Qualquer
    falha desfaz tudo (rollback)."""
    try:
        req = session.get(StockRequest, request_id)
        if not req:
            raise HTTPException(404, "solicitação não encontrada")
        if req.status != PENDING:
            raise HTTPException(409, f"solicitação já está {req.status}")

        product = session.get(Product, req.product_id)
        if not product:
            raise HTTPException(404, "produto não encontrado")

        # Estoque central disponível na unidade pedida (revalidado no momento
        # da aprovação — pode ter mudado desde a solicitação).
        available = getattr(product, req.unidade) or 0
        if available < req.quantity:
            raise HTTPException(409, "estoque central insuficiente para aprovar")

        # Debita do central e cria a retirada para o ponto de destino.
        setattr(product, req.unidade, available - req.quantity)
        retirada = RetiradaProduto(
            sale_point_id=req.target_point_id,
            product_id=req.product_id,
            taken_quantity=req.quantity,
            unidade=req.unidade,
            observacao=f"Reposição aprovada (solicitação #{req.id})",
            data=_now(),
            sold_quantity=0,
            total_value=req.quantity * (product.price or 0),
            status=True,
            remaining_quantity=req.quantity,
        )
        session.add(retirada)
        session.flush()  # garante retirada.id para vincular abaixo

        req.status = APPROVED
        req.decided_at = _now()
        req.decided_by_id = admin_id
        req.applied_outbound_id = retirada.id

        session.commit()
        session.refresh(req)
        return _to_response(req)
    except Exception:
        session.rollback()
        raise


def reject_stock_request_service(session, admin_id: int, request_id: int, reason: str):
    if not reason or not reason.strip():
        raise HTTPException(400, "motivo da recusa é obrigatório")
    req = session.get(StockRequest, request_id)
    if not req:
        raise HTTPException(404, "solicitação não encontrada")
    if req.status != PENDING:
        raise HTTPException(409, f"solicitação já está {req.status}")

    req.status = REJECTED
    req.reason = reason
    req.decided_at = _now()
    req.decided_by_id = admin_id
    session.commit()
    session.refresh(req)
    return _to_response(req)


def set_point_stock_service(session, point_id: int, data: StockRequestCreateDTO):
    """Ajuste DIRETO de estoque pelo admin: define o estoque disponível de um
    produto em um ponto, sem passar por aprovação. Faz upsert da retirada do
    dia (cria se não existir, sobrescreve a quantidade se existir)."""
    if data.unidade not in VALID_UNITS:
        raise HTTPException(400, "unidade inválida (use amount, kg ou liters)")
    if data.quantity < 0:
        raise HTTPException(400, "quantidade não pode ser negativa")
    product = session.get(Product, data.product_id)
    if not product:
        raise HTTPException(404, "produto não encontrado")

    retirada = session.query(RetiradaProduto).filter(
        RetiradaProduto.sale_point_id == point_id,
        RetiradaProduto.product_id == data.product_id,
        func.date(RetiradaProduto.data) == date.today(),
    ).first()

    if retirada:
        # mantém o que já foi vendido; redefine o disponível
        retirada.remaining_quantity = data.quantity
        retirada.taken_quantity = (retirada.sold_quantity or 0) + data.quantity
        retirada.unidade = data.unidade
    else:
        retirada = RetiradaProduto(
            sale_point_id=point_id,
            product_id=data.product_id,
            taken_quantity=data.quantity,
            unidade=data.unidade,
            observacao="Ajuste de estoque pelo administrador",
            data=_now(),
            sold_quantity=0,
            total_value=0,
            status=True,
            remaining_quantity=data.quantity,
        )
        session.add(retirada)

    session.commit()
    session.refresh(retirada)
    return {
        "sale_point_id": point_id,
        "product_id": data.product_id,
        "product_name": product.name,
        "unidade": retirada.unidade,
        "remaining_quantity": retirada.remaining_quantity,
    }


def cancel_stock_request_service(session, user, request_id: int):
    req = session.get(StockRequest, request_id)
    if not req:
        raise HTTPException(404, "solicitação não encontrada")
    if user.get("role") != "admin" and req.target_point_id != user.get("sale_point_id"):
        raise HTTPException(403, "acesso negado")
    if req.status != PENDING:
        raise HTTPException(409, f"solicitação já está {req.status}")

    req.status = CANCELLED
    req.decided_at = _now()
    session.commit()
    session.refresh(req)
    return _to_response(req)
