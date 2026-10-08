from datetime import date as Date
from typing import Optional, Annotated

from dependencies.dependencies import make_session
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status, Path
from schemas.input_dto import RequestParameters
from exceptions.order_exceptions import AdminPermissionRequired, OrderNotFoundException
from schemas.order_schema import ENDPOINT_DOCS, ListOrderQueryDTO, OrderResponseDTO, OrderUpdateDTO, OrderRequestDTO
from services.order_service import delete_all_orders_service, delete_order, edit_order, search_order, list_orders_service
from dependencies.sale_point_dependencies import validate_token


order_router = APIRouter(prefix='/orders', tags=['Orders'])


@order_router.get('', response_model=list[OrderResponseDTO], response_model_by_alias=False, status_code=status.HTTP_200_OK)
def index(
    date: Optional[Date] = None,
    description: Optional[str] = None,
    status: Optional[bool] = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1),
    user=Depends(validate_token),
    session=Depends(make_session, use_cache=False),
):
    return list_orders_service(session, date, status, description, page=page, size=size)


@order_router.get('/{id}', response_model=OrderResponseDTO, response_model_by_alias=False, status_code=status.HTTP_200_OK)
def show(id: Annotated[int, Path(gt=0)], user=Depends(validate_token), session=Depends(make_session, use_cache=False)):
    try:
        return search_order(session, user, id)
    except OrderNotFoundException as error:
        raise HTTPException(404, detail=str(error)) from error
    

@order_router.patch('/{id}', response_model=OrderResponseDTO, response_model_by_alias=False)
async def edit(id: Annotated[int, Path(gt=0)], http_request: Request, user=Depends(validate_token), session=Depends(make_session, use_cache=False)):
    try:
        request = OrderUpdateDTO.from_payload(await http_request.json())
        return edit_order(session, id, request)
    except OrderNotFoundException as error:
        raise HTTPException(404, detail=str(error)) from error
    except (ValueError, TypeError) as error:
        raise HTTPException(422, detail=str(error)) from error


@order_router.delete('/{id}', status_code=status.HTTP_200_OK, response_model=OrderResponseDTO, response_model_by_alias=False)
async def delete(id: Annotated[int, Path(gt=0)], user=Depends(validate_token), session=Depends(make_session, use_cache=False)):
    try:  
        return delete_order(id, session, user)
    except AdminPermissionRequired as error:
        raise HTTPException(403, detail=str(error)) from error
    except OrderNotFoundException as error:
        raise HTTPException(404, detail=str(error)) from error


@order_router.delete('', status_code=status.HTTP_200_OK, response_model=list[OrderResponseDTO], response_model_by_alias=False)
async def delete_all_orders(user=Depends(validate_token), session=Depends(make_session, use_cache=False)):
    try:
        return delete_all_orders_service(session, user)
    except AdminPermissionRequired as error:
        raise HTTPException(403, detail=str(error)) from error
