from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from controllers.auth_controller import auth_router
from controllers.sale_point_controller import sale_point_router
from controllers.outbound_controller import outbound_router
from controllers.order_controller import order_router
from controllers.product_controller import product_router
from fastapi.middleware.cors import CORSMiddleware
from logging_config import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)
app = FastAPI()


@app.exception_handler(RequestValidationError)
@app.exception_handler(StarletteHTTPException)
@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    headers = None
    if isinstance(exc, RequestValidationError):
        status_code = 422
        detail = exc.errors()
    elif isinstance(exc, StarletteHTTPException):
        status_code = exc.status_code
        detail = exc.detail
        headers = exc.headers
    else:
        status_code = 500
        detail = 'Erro interno do servidor'

    logger.warning(
        'Erro em %s %s: %s',
        request.method,
        request.url.path,
        exc,
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    return JSONResponse(
        status_code=status_code,
        content={'detail': jsonable_encoder(detail)},
        headers=headers,
    )


app.include_router(auth_router)
app.include_router(sale_point_router)
app.include_router(order_router)
app.include_router(product_router)
app.include_router(outbound_router)

origins = [
    "http://localhost:5173", 
    "http://127.0.0.1:5173",
    "http://localhost:8080", 
    "http://127.0.0.1:8080",
    "http://localhost:58000",
    "http://127.0.0.1:58000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,  
    allow_methods=["*"],
    allow_headers=["*"],  
    expose_headers=["*"]  
)
