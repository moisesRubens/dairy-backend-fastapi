from dependencies.dependencies import make_session
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from schemas.input_dto import RequestParameters
from exceptions.product_exceptions import BusinessConflict, ExistingProductException, ProductNotFound
from schemas.product_schema import ENDPOINT_DOCS, ListProductQueryDTO, ProductRequestDTO, ProductResponseDTO, ProductUpdateDTO
from services.product_service import create_product_service, delete_all_products_service, delete_product_service, edit_product_service, get_all_products_service, get_product_service
from dependencies.sale_point_dependencies import validate_token
from exceptions.common_exceptions import AdminPermissionRequired
product_router = APIRouter(prefix='/products', tags=['Products'])

@product_router.get('', response_model=list[ProductResponseDTO], openapi_extra=ENDPOINT_DOCS['index'])
async def list_product_controller(http_request: Request, *, user=Depends(validate_token), session=Depends(make_session, use_cache=False)):
    try:
        parameters = ListProductQueryDTO.from_payload(dict(http_request.query_params))
        products = await get_all_products_service(session, limit=parameters.limit, offset=parameters.offset)
        return products
    except HTTPException:
        raise
    except (ValueError, TypeError) as error:
        raise HTTPException(422, detail=str(error)) from error

@product_router.post('', status_code=201, response_model=list[ProductResponseDTO], openapi_extra=ENDPOINT_DOCS['store'])
async def create_product_controller(http_request: Request, *, user=Depends(validate_token), session=Depends(make_session, use_cache=False)):
    try:
        producst_list_request = ProductRequestDTO.from_list(await http_request.json())
        product_data = create_product_service(producst_list_request, session)
        return product_data
    except HTTPException:
        raise
    except (BusinessConflict, ExistingProductException) as error:
        raise HTTPException(409, detail=str(error)) from error
    except (ValueError, TypeError) as error:
        raise HTTPException(422, detail=str(error)) from error

@product_router.delete('/{id}', status_code=200, response_model=ProductResponseDTO)
async def delete_product_controller(http_request: Request, *, user=Depends(validate_token), session=Depends(make_session, use_cache=False)):
    try:
        id = RequestParameters.positive_id(http_request.path_params.get('id'))
        return delete_product_service(session, id, user)
    except HTTPException:
        raise
    except ProductNotFound as error:
        raise HTTPException(404, detail=str(error)) from error
    except AdminPermissionRequired as error:
        raise HTTPException(403, detail=str(error)) from error
    except (ValueError, TypeError) as error:
        raise HTTPException(422, detail=str(error)) from error

@product_router.get('/{id}', response_model=ProductResponseDTO, openapi_extra=ENDPOINT_DOCS['show'])
async def get_product_controller(http_request: Request, *, user=Depends(validate_token), session=Depends(make_session, use_cache=False)):
    try:
        id = RequestParameters.positive_id(http_request.path_params.get('id'))
        result = get_product_service(session, id)
        return result
    except HTTPException:
        raise
    except ProductNotFound as error:
        raise HTTPException(404, detail=str(error)) from error
    except (ValueError, TypeError) as error:
        raise HTTPException(422, detail=str(error)) from error

@product_router.patch('/{id}', response_model=ProductResponseDTO, openapi_extra=ENDPOINT_DOCS['edit'])
async def edit_product_controller(http_request: Request, *, user=Depends(validate_token), session=Depends(make_session, use_cache=False)):
    try:
        product_request = ProductUpdateDTO.from_payload(await http_request.json())
        id = RequestParameters.positive_id(http_request.path_params.get('id'))
        result = edit_product_service(session, id, product_request)
        return result
    except HTTPException:
        raise
    except ProductNotFound as error:
        raise HTTPException(404, detail=str(error)) from error
    except ExistingProductException as error:
        raise HTTPException(409, detail=str(error)) from error
    except (ValueError, TypeError) as error:
        raise HTTPException(422, detail=str(error)) from error

@product_router.delete('', status_code=200, response_model=list[ProductResponseDTO])
async def delete_all_product_controller(http_request: Request, *, user=Depends(validate_token), session=Depends(make_session, use_cache=False)):
    try:
        return delete_all_products_service(session, user)
    except HTTPException:
        raise
    except AdminPermissionRequired as error:
        raise HTTPException(403, detail=str(error)) from error
    except (ValueError, TypeError) as error:
        raise HTTPException(422, detail=str(error)) from error
