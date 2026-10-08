from dependencies.dependencies import make_session
from fastapi import APIRouter, Depends, HTTPException, Request
from schemas.input_dto import RequestParameters
from exceptions.outbound_exceptions import OutboundNotFound
from schemas.outbound_schema import ENDPOINT_DOCS, ListOutboundQueryDTO, OutboundRequestDTO, SalePointDailyOutboundsDTO
from services.outbound_service import edit_outbound_service, get_all_products_by_sale_point_service, get_outbound_service
from exceptions.product_exceptions import BusinessConflict, InsuficientProductsAmountException, ProductNotFound
from schemas.product_schema import ItemsRetiradaResponseDTO
from dependencies.sale_point_dependencies import validate_token
outbound_router = APIRouter(prefix='/outbounds', tags=['Outbounds'])

@outbound_router.get('', response_model=list[SalePointDailyOutboundsDTO], openapi_extra=ENDPOINT_DOCS['index'])
async def list_outbound_controller(http_request: Request, *, user=Depends(validate_token), session=Depends(make_session, use_cache=False)):
    try:
        parameters = ListOutboundQueryDTO.from_payload(dict(http_request.query_params))
        return await get_all_products_by_sale_point_service(session, parameters.date, False)
    except HTTPException:
        raise
    except (ValueError, TypeError) as error:
        raise HTTPException(422, detail=str(error)) from error

@outbound_router.get('/{id}', response_model=ItemsRetiradaResponseDTO, openapi_extra=ENDPOINT_DOCS['show'])
async def get_outbound_controller(http_request: Request, *, user=Depends(validate_token), session=Depends(make_session, use_cache=False)):
    try:
        id = RequestParameters.positive_id(http_request.path_params.get('id'))
        return get_outbound_service(session, id)
    except HTTPException:
        raise
    except OutboundNotFound as error:
        raise HTTPException(404, detail=str(error)) from error
    except (ValueError, TypeError) as error:
        raise HTTPException(422, detail=str(error)) from error

@outbound_router.patch('/{id}', response_model=ItemsRetiradaResponseDTO, openapi_extra=ENDPOINT_DOCS['edit_outbound'])
async def edit_outbound_controller(http_request: Request, *, user=Depends(validate_token), session=Depends(make_session, use_cache=False)):
    try:
        outbound_request = OutboundRequestDTO.from_payload(await http_request.json())
        id = RequestParameters.positive_id(http_request.path_params.get('id'))
        return edit_outbound_service(session, id, outbound_request)
    except HTTPException:
        raise
    except (OutboundNotFound, ProductNotFound) as error:
        raise HTTPException(404, detail=str(error)) from error
    except (BusinessConflict, InsuficientProductsAmountException) as error:
        raise HTTPException(409, detail=str(error)) from error
    except (ValueError, TypeError) as error:
        raise HTTPException(422, detail=str(error)) from error
