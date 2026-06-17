from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import HTTPException
from sqlalchemy import func
from model import Client, Order
from clients.client_schema import ClientCreateDTO, ClientUpdateDTO, ClientResponseDTO


def _is_admin(user) -> bool:
    return user.get("role") == "admin"


def _load_owned(session, user, client_id: int) -> Client:
    client = session.get(Client, client_id)
    if not client:
        raise HTTPException(404, "cliente não encontrado")
    if not _is_admin(user) and client.sale_point_id != user.get("sale_point_id"):
        raise HTTPException(403, "acesso negado a cliente de outro ponto")
    return client


def create_client_service(session, sale_point_id: int, data: ClientCreateDTO):
    client = Client(
        name=data.name.strip(),
        phone=data.phone,
        email=data.email,
        notes=data.notes,
        sale_point_id=sale_point_id,
        created_at=datetime.now(tz=ZoneInfo("America/Sao_Paulo")),
    )
    session.add(client)
    session.commit()
    session.refresh(client)
    return ClientResponseDTO.model_validate(client)


def list_clients_service(session, user):
    query = session.query(Client)
    if not _is_admin(user):
        query = query.filter(Client.sale_point_id == user.get("sale_point_id"))
    clients = query.order_by(Client.name.asc()).all()
    return [ClientResponseDTO.model_validate(c) for c in clients]


def get_client_service(session, user, client_id: int):
    return ClientResponseDTO.model_validate(_load_owned(session, user, client_id))


def update_client_service(session, user, client_id: int, data: ClientUpdateDTO):
    client = _load_owned(session, user, client_id)
    if data.name is not None:
        client.name = data.name.strip()
    if data.phone is not None:
        client.phone = data.phone
    if data.email is not None:
        client.email = data.email
    if data.notes is not None:
        client.notes = data.notes
    session.commit()
    session.refresh(client)
    return ClientResponseDTO.model_validate(client)


def delete_client_service(session, user, client_id: int):
    client = _load_owned(session, user, client_id)
    session.delete(client)
    session.commit()
    return {"message": "cliente removido"}


def client_history_service(session, user, client_id: int):
    """Histórico de compras do cliente + total gasto (base do relacionamento)."""
    _load_owned(session, user, client_id)
    orders = session.query(Order).filter(Order.client_id == client_id) \
        .order_by(Order.order_date.desc()).all()
    total = sum((o.total_value or 0) for o in orders)
    return {
        "client_id": client_id,
        "orders_count": len(orders),
        "total_spent": round(float(total), 2),
        "orders": [
            {
                "id": o.id,
                "total_value": round(float(o.total_value or 0), 2),
                "date": o.order_date,
            }
            for o in orders
        ],
    }


def clients_ranking_service(session):
    """Ranking de melhores clientes por total gasto (admin)."""
    rows = session.query(
        Client.id, Client.name, Client.sale_point_id,
        func.coalesce(func.sum(Order.total_value), 0.0),
        func.count(Order.id),
    ).outerjoin(Order, Order.client_id == Client.id) \
     .group_by(Client.id, Client.name, Client.sale_point_id) \
     .order_by(func.coalesce(func.sum(Order.total_value), 0.0).desc()).all()

    return [
        {
            "client_id": cid,
            "name": name,
            "sale_point_id": spid,
            "total_spent": round(float(total or 0), 2),
            "orders_count": int(count or 0),
        }
        for cid, name, spid, total, count in rows
    ]
