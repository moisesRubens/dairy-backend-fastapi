from fastapi import APIRouter, Depends
from dependencies import make_session
from sales_points.sale_point_dependencies import validate_token, require_admin
from clients.client_schema import ClientCreateDTO, ClientUpdateDTO
from clients import client_service as svc

client_router = APIRouter(prefix="/clients", tags=["Client"])


@client_router.post("/", status_code=201)
async def create(data: ClientCreateDTO, user = Depends(validate_token), session = Depends(make_session)):
    # Cliente é cadastrado para o ponto do usuário logado.
    return svc.create_client_service(session, user["sale_point_id"], data)


@client_router.get("/")
async def index(user = Depends(validate_token), session = Depends(make_session)):
    # Admin vê todos; vendedor vê só os clientes do próprio ponto.
    return svc.list_clients_service(session, user)


@client_router.get("/ranking")
async def ranking(user = Depends(require_admin), session = Depends(make_session)):
    # Declarado antes de /{id} para não cair na rota paramétrica.
    return svc.clients_ranking_service(session)


@client_router.get("/{client_id}")
async def show(client_id: int, user = Depends(validate_token), session = Depends(make_session)):
    return svc.get_client_service(session, user, client_id)


@client_router.patch("/{client_id}")
async def update(client_id: int, data: ClientUpdateDTO, user = Depends(validate_token), session = Depends(make_session)):
    return svc.update_client_service(session, user, client_id, data)


@client_router.delete("/{client_id}")
async def destroy(client_id: int, user = Depends(validate_token), session = Depends(make_session)):
    return svc.delete_client_service(session, user, client_id)


@client_router.get("/{client_id}/orders")
async def history(client_id: int, user = Depends(validate_token), session = Depends(make_session)):
    return svc.client_history_service(session, user, client_id)
