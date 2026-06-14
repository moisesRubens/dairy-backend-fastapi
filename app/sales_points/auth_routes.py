from typing import Annotated
from typing import Optional
from fastapi import APIRouter, Depends, Response, status
from starlette.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sales_points.sale_point_dependencies import make_session, validate_token, oauth2_scheme, require_admin, require_self_or_admin
from sales_points.sale_point_controller import get_all_sales_points_controller, login_controller, create_sale_point_controller, get_sale_point, delete_sale_point_controller, logout_controller, delete_all_sales_points_controller, get_outbounds_controller, create_outbound_controller, delete_outbounds_controller, return_outbounds_controller, delete_orders_controller, bootstrap_admin_controller
from orders.order_controller import get_orders_by_sale_point_id_controller, create_order_controller
from orders.order_schema import OrderRequestDTO
from products.product_schema import RetirarProdutosRequestDTO
from datetime import date

auth_router = APIRouter(prefix="/auth", tags=["Auth"])

@auth_router.get("/")
async def index(user = Depends(require_admin), session = (Depends(make_session))):
    # Listar todos os pontos de venda é operação de administrador.
    return await get_all_sales_points_controller(session)


@auth_router.post("/", status_code=201)
async def store(name: str, password: str, email: str = None, user = Depends(require_admin), session = Depends(make_session)):
    # P0: cadastro deixou de ser aberto. Apenas um admin cria novos vendedores.
    sale_point_data = await create_sale_point_controller(name, email, password, session)
    return sale_point_data


@auth_router.post("/bootstrap-admin", status_code=201)
async def bootstrap_admin(name: str, password: str, email: str = None, session = Depends(make_session)):
    # Cria o PRIMEIRO administrador. Fica disponível apenas enquanto não houver
    # nenhum admin; depois retorna 403. É como o sistema sai do zero com segurança.
    return await bootstrap_admin_controller(name, email, password, session)


@auth_router.delete("/")
async def delete_all(user = Depends(require_admin), session = Depends(make_session)):
    # P0: antes qualquer vendedor logado apagava TODOS os pontos. Só admin.
    await delete_all_sales_points_controller(session)
    return {"message": "Sales points excluded"}


@auth_router.get("/{id}")  
async def show(id: int, user = Depends(require_self_or_admin), session = Depends(make_session)):
    sale_point = await get_sale_point(id, session)
    return sale_point


@auth_router.delete("/{id}") 
async def destroy(
    id: int,
    token: Annotated[str, Depends(oauth2_scheme)],
    user = Depends(require_admin),
    session = Depends(make_session)
):
    sale_point_response = await delete_sale_point_controller(id, token, session)
    return {"sale point deleted": sale_point_response}


@auth_router.get("/{id}/order") 
async def get_orders_by_sale_point_id(
    id: int,
    date: Optional[str] = None,
    user = Depends(require_self_or_admin),
    session = Depends(make_session)
):
    result = await get_orders_by_sale_point_id_controller(session, date, id)
    return result


@auth_router.post("/{id}/order", status_code=201)
async def store_order(id:int, request_data: OrderRequestDTO, user = Depends(require_self_or_admin), session = Depends(make_session)):
    result = await create_order_controller(request_data, id, session)
    return result


@auth_router.delete("/{id}/order")
async def delete_orders(id: int, user = Depends(require_self_or_admin), session = Depends(make_session)):
    return await delete_orders_controller(session, id)


@auth_router.get("/{id}/outbounds")
async def get_outbounds(id: int, date: Optional[date] = None,  user = Depends(require_self_or_admin), session = Depends(make_session)):
    result = await get_outbounds_controller(id, date, session)
    return result


@auth_router.post("/{id}/outbounds", status_code=201)
async def create_outbound(
    id: int,
    request: RetirarProdutosRequestDTO,
    user = Depends(require_self_or_admin),
    session = Depends(make_session)
):
    result = await create_outbound_controller(session, id, request)
    return result


@auth_router.delete("/{id}/outbounds")
async def delete_outbounds(id:int, user = Depends(require_admin), session = Depends(make_session)):
    return await delete_outbounds_controller(session, id)


@auth_router.patch("/{id}/outbounds")
async def return_outbounds(id: int, user = Depends(require_self_or_admin), session = Depends(make_session)):
    return await return_outbounds_controller(session, id)


@auth_router.post("/login", status_code=201)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session = Depends(make_session)):
    token = await login_controller(form_data, session)
    return {"access_token": token, "token_type": "bearer"}


@auth_router.post("/logout")  
async def logout(
    token: Annotated[str, Depends(oauth2_scheme)], 
    user_data = Depends(validate_token), 
    session = Depends(make_session)
):
    await logout_controller(token, session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)