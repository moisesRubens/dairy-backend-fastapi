from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from schemas.input_dto import RequestParameters
from exceptions.common_exceptions import AdminPermissionRequired, PermissionDenied
from services.authorization import require_admin
from database.model import SalePoints
from schemas.order_schema import OrderRequestDTO, OrderResponseDTO
from services.order_service import create_order_service, get_orders_by_sale_point_id_service
from schemas.outbound_schema import SalePointOutboundsDTO
from exceptions.product_exceptions import BusinessConflict, InsuficientProductsAmountException, ProductNotFound
from schemas.product_schema import ItemsRetiradaResponseDTO, RetirarProdutosRequestDTO
from services.product_service import get_products_by_sale_point_service
from services.report_service import chart_report, export_report
from dependencies.sale_point_dependencies import make_session, validate_token
from exceptions.sale_point_exceptions import ExistingSalePointException, SalePointNotFound
from schemas.sale_point_schema import DeleteOutboundsSalePointQueryDTO, ENDPOINT_DOCS, ExportSalesReportSalePointQueryDTO, GetOrdersBySalePointIdSalePointQueryDTO, GetOutboundsSalePointQueryDTO, SalePointCreateDTO, SalePointRequestDTO, SalePointResponseDTO, SalePointUpdateDTO, SalesChartsSalePointQueryDTO
from services.sale_point_service import create_outbound_service, create_sale_point_service, delete_all_sales_points_service, delete_orders_service, delete_outbounds_service, delete_sale_point_service, edit_sale_point_service, get_all_sales_points_service, get_sale_point_service, return_outbounds_service
sale_point_router = APIRouter(prefix='/sale-points', tags=['Sale points'])

@sale_point_router.get('', response_model=list[SalePointResponseDTO], openapi_extra=ENDPOINT_DOCS['index'])
async def list_sale_point_controller(http_request: Request, *, user=Depends(validate_token), session=Depends(make_session, use_cache=False)):
    try:
        return get_all_sales_points_service(session)
    except HTTPException:
        raise
    except (ValueError, TypeError) as error:
        raise HTTPException(422, detail=str(error)) from error

@sale_point_router.post('', status_code=status.HTTP_201_CREATED, response_model=SalePointResponseDTO, openapi_extra=ENDPOINT_DOCS['store'])
async def create_sale_point_controller(http_request: Request, *, response: Response, session=Depends(make_session, use_cache=False)):
    try:
        request = SalePointCreateDTO.from_payload(await http_request.json())
        sale_point_data = await create_sale_point_service(SalePointRequestDTO(name=request.name, email=request.email, password=request.password), session)
        response.headers['Location'] = f'/sale-points/{sale_point_data.id}'
        return sale_point_data
    except HTTPException:
        raise
    except ExistingSalePointException as error:
        raise HTTPException(409, detail=str(error)) from error
    except (ValueError, TypeError) as error:
        raise HTTPException(422, detail=str(error)) from error

@sale_point_router.patch('/{id}', response_model=SalePointResponseDTO, openapi_extra=ENDPOINT_DOCS['edit'])
async def edit_sale_point_controller(http_request: Request, *, user=Depends(validate_token), session=Depends(make_session, use_cache=False)):
    try:
        request = SalePointUpdateDTO.from_payload(await http_request.json())
        id = RequestParameters.positive_id(http_request.path_params.get('id'))
        sale_point_data = await edit_sale_point_service(id, request, session, user)
        return sale_point_data
    except (AdminPermissionRequired, PermissionDenied) as error:
        raise HTTPException(403, detail=str(error)) from error
    except HTTPException:
        raise
    except SalePointNotFound as error:
        raise HTTPException(404, detail=str(error)) from error
    except ExistingSalePointException as error:
        raise HTTPException(409, detail=str(error)) from error
    except (ValueError, TypeError) as error:
        raise HTTPException(422, detail=str(error)) from error

@sale_point_router.delete('', status_code=status.HTTP_200_OK, response_model=list[SalePointResponseDTO])
async def delete_all_sale_point_controller(http_request: Request, *, user=Depends(validate_token), session=Depends(make_session, use_cache=False)):
    try:
        return delete_all_sales_points_service(session, user)
    except (AdminPermissionRequired, PermissionDenied) as error:
        raise HTTPException(403, detail=str(error)) from error
    except HTTPException:
        raise
    except (ValueError, TypeError) as error:
        raise HTTPException(422, detail=str(error)) from error

@sale_point_router.get('/reports/charts', openapi_extra=ENDPOINT_DOCS['sales_charts'])
async def sales_charts_sale_point_controller(http_request: Request, *, user=Depends(validate_token), session=Depends(make_session, use_cache=False)):
    try:
        parameters = SalesChartsSalePointQueryDTO.from_payload(dict(http_request.query_params))
        require_admin(session, user, 'Somente administradores podem consultar dados')
        return chart_report(session, parameters.day, parameters.period)
    except (AdminPermissionRequired, PermissionDenied) as error:
        raise HTTPException(403, detail=str(error)) from error
    except HTTPException:
        raise
    except (ValueError, TypeError) as error:
        raise HTTPException(422, detail=str(error)) from error

@sale_point_router.get('/reports/export', openapi_extra=ENDPOINT_DOCS['export_sales_report'])
async def export_sales_report_sale_point_controller(http_request: Request, *, user=Depends(validate_token), session=Depends(make_session, use_cache=False)):
    try:
        parameters = ExportSalesReportSalePointQueryDTO.from_payload(dict(http_request.query_params))
        require_admin(session, user, 'Somente administradores podem exportar dados')
        content, filename = export_report(session, parameters.day, parameters.period)
        return Response(content=content, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={'Content-Disposition': f'attachment; filename="{filename}"'})
    except (AdminPermissionRequired, PermissionDenied) as error:
        raise HTTPException(403, detail=str(error)) from error
    except HTTPException:
        raise
    except (ValueError, TypeError) as error:
        raise HTTPException(422, detail=str(error)) from error

@sale_point_router.get('/{id}', response_model=SalePointResponseDTO, openapi_extra=ENDPOINT_DOCS['show'])
async def get_sale_point_controller(http_request: Request, *, user=Depends(validate_token), session=Depends(make_session, use_cache=False)):
    try:
        id = RequestParameters.positive_id(http_request.path_params.get('id'))
        sale_point = await get_sale_point_service(id, session)
        return sale_point
    except HTTPException:
        raise
    except SalePointNotFound as error:
        raise HTTPException(404, detail=str(error)) from error
    except (ValueError, TypeError) as error:
        raise HTTPException(422, detail=str(error)) from error

@sale_point_router.delete('/{id}', status_code=status.HTTP_200_OK, response_model=SalePointResponseDTO)
async def delete_sale_point_controller(http_request: Request, *, user=Depends(validate_token), session=Depends(make_session, use_cache=False)):
    try:
        id = RequestParameters.positive_id(http_request.path_params.get('id'))
        return await delete_sale_point_service(id, session, user)
    except (AdminPermissionRequired, PermissionDenied) as error:
        raise HTTPException(403, detail=str(error)) from error
    except HTTPException:
        raise
    except SalePointNotFound as error:
        raise HTTPException(404, detail=str(error)) from error
    except (ValueError, TypeError) as error:
        raise HTTPException(422, detail=str(error)) from error

@sale_point_router.get('/{id}/orders', response_model=list[OrderResponseDTO], response_model_by_alias=False, openapi_extra=ENDPOINT_DOCS['get_orders_by_sale_point_id'])
async def get_orders_by_sale_point_id_sale_point_controller(http_request: Request, *, user=Depends(validate_token), session=Depends(make_session, use_cache=False)):
    try:
        id = RequestParameters.positive_id(http_request.path_params.get('id'))
        parameters = GetOrdersBySalePointIdSalePointQueryDTO.from_payload(dict(http_request.query_params))
        result = get_orders_by_sale_point_id_service(session, parameters.date, id, since=parameters.since, include_pending=parameters.include_pending, limit=parameters.limit, offset=parameters.offset)
        return result
    except HTTPException:
        raise
    except SalePointNotFound as error:
        raise HTTPException(404, detail=str(error)) from error
    except (ValueError, TypeError) as error:
        raise HTTPException(422, detail=str(error)) from error

@sale_point_router.post('/{id}/orders', status_code=201, response_model=OrderResponseDTO, response_model_by_alias=False, openapi_extra=ENDPOINT_DOCS['store_order'])
async def store_order_sale_point_controller(http_request: Request, *, response: Response, user=Depends(validate_token), session=Depends(make_session, use_cache=False)):
    try:
        id = RequestParameters.positive_id(http_request.path_params.get('id'))
        request_data = OrderRequestDTO.from_payload(await http_request.json())
        result = create_order_service(request_data, id, session)
        response.headers['Location'] = f'/orders/{result.id}'
        return result
    except HTTPException:
        raise
    except (ProductNotFound, SalePointNotFound) as error:
        raise HTTPException(404, detail=str(error)) from error
    except (BusinessConflict, InsuficientProductsAmountException) as error:
        raise HTTPException(409, detail=str(error)) from error
    except (ValueError, TypeError) as error:
        raise HTTPException(422, detail=str(error)) from error

@sale_point_router.delete('/{id}/orders', openapi_extra=ENDPOINT_DOCS['delete_orders'])
async def delete_orders_sale_point_controller(http_request: Request, *, user=Depends(validate_token), session=Depends(make_session, use_cache=False)):
    try:
        id = RequestParameters.positive_id(http_request.path_params.get('id'))
        return await delete_orders_service(session, id, user)
    except SalePointNotFound as error:
        raise HTTPException(404, detail=str(error)) from error
    except (AdminPermissionRequired, PermissionDenied) as error:
        raise HTTPException(403, detail=str(error)) from error
    except HTTPException:
        raise
    except (ValueError, TypeError) as error:
        raise HTTPException(422, detail=str(error)) from error

@sale_point_router.get('/{id}/outbounds', response_model=SalePointOutboundsDTO, openapi_extra=ENDPOINT_DOCS['get_outbounds'])
async def get_outbounds_sale_point_controller(http_request: Request, *, user=Depends(validate_token), session=Depends(make_session, use_cache=False)):
    try:
        id = RequestParameters.positive_id(http_request.path_params.get('id'))
        parameters = GetOutboundsSalePointQueryDTO.from_payload(dict(http_request.query_params))
        result = await get_products_by_sale_point_service(id, session, parameters.date, False, since=parameters.since, include_open=parameters.include_open, limit=parameters.limit, offset=parameters.offset)
        return result
    except HTTPException:
        raise
    except SalePointNotFound as error:
        raise HTTPException(404, detail=str(error)) from error
    except (ValueError, TypeError) as error:
        raise HTTPException(422, detail=str(error)) from error

@sale_point_router.post('/{id}/outbounds', status_code=201, response_model=list[ItemsRetiradaResponseDTO], openapi_extra=ENDPOINT_DOCS['create_outbound'])
async def create_outbound_sale_point_controller(http_request: Request, *, user=Depends(validate_token), session=Depends(make_session, use_cache=False)):
    try:
        id = RequestParameters.positive_id(http_request.path_params.get('id'))
        request = RetirarProdutosRequestDTO.from_payload(await http_request.json())
        result = await create_outbound_service(session, id, request)
        return result
    except HTTPException:
        raise
    except (ProductNotFound, SalePointNotFound) as error:
        raise HTTPException(404, detail=str(error)) from error
    except (BusinessConflict, InsuficientProductsAmountException) as error:
        raise HTTPException(409, detail=str(error)) from error
    except (ValueError, TypeError) as error:
        raise HTTPException(422, detail=str(error)) from error

@sale_point_router.delete('/{id}/outbounds', openapi_extra=ENDPOINT_DOCS['delete_outbounds'])
async def delete_outbounds_sale_point_controller(http_request: Request, *, user=Depends(validate_token), session=Depends(make_session, use_cache=False)):
    try:
        id = RequestParameters.positive_id(http_request.path_params.get('id'))
        parameters = DeleteOutboundsSalePointQueryDTO.from_payload(dict(http_request.query_params))
        'Encerra as retiradas ativas e devolve o saldo, preservando o historico.'
        return await delete_outbounds_service(session, id, user, parameters.before)
    except (AdminPermissionRequired, PermissionDenied) as error:
        raise HTTPException(403, detail=str(error)) from error
    except HTTPException:
        raise
    except (ProductNotFound, SalePointNotFound) as error:
        raise HTTPException(404, detail=str(error)) from error
    except (ValueError, TypeError) as error:
        raise HTTPException(422, detail=str(error)) from error

@sale_point_router.patch('/{id}/outbounds', openapi_extra=ENDPOINT_DOCS['return_outbounds'])
async def return_outbounds_sale_point_controller(http_request: Request, *, user=Depends(validate_token), session=Depends(make_session, use_cache=False)):
    try:
        id = RequestParameters.positive_id(http_request.path_params.get('id'))
        return await return_outbounds_service(session, id)
    except HTTPException:
        raise
    except (ProductNotFound, SalePointNotFound) as error:
        raise HTTPException(404, detail=str(error)) from error
    except (ValueError, TypeError) as error:
        raise HTTPException(422, detail=str(error)) from error
