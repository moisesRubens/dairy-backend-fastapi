from fastapi import APIRouter, Depends
from dependecies import make_session
from products.product_schema import RetirarProdutosRequestDTO
from sales_points.sale_point_dependencies import validate_token
from products.product_controller import delete_product_controller, create_product_controller, get_all_products_controller, delete_all_products_controller, retirar_produtos_controller, get_all_retiradas_controller

product_router = APIRouter(prefix="/produto", tags=["Product"])

@product_router.get("/")
async def index(user = Depends(validate_token), session = Depends(make_session)):
    products = get_all_products_controller(session)
    return {"products": products}

@product_router.post("/retirar")
async def retirar_produtos(
    request: RetirarProdutosRequestDTO,
    user = Depends(validate_token),
    session = Depends(make_session)
):
    """
    Retira produtos do estoque total e associa ao ponto de venda.
    Recebe uma lista de produtos com suas quantidades.
    """
    result = retirar_produtos_controller(session, user['sub'], request.produtos)
    return result

@product_router.get("/retiradas")
async def list_all_retiradas(
    user = Depends(validate_token),
    session = Depends(make_session)
):
    """
    Lista todas as retiradas de produtos (histórico completo)
    """
    result = get_all_retiradas_controller(session)
    return {"retiradas": result}

@product_router.post("/cadastrar")
async def store(name: str, price: float, amount: int = None, kg: float = None, liters: float = None, user = Depends(validate_token), session = Depends(make_session)):
    product_data = create_product_controller(name, price, amount, kg, liters,session)
    return {"product created": product_data}

@product_router.delete("/{id}")
async def destroy(id: int, user = Depends(validate_token), session = Depends(make_session)):
    product_data = delete_product_controller(session, id)
    return {"Produto excluido": product_data}


@product_router.delete("/")
async def delete_all(user = Depends(validate_token), session = Depends(make_session)):
    delete_all_products_controller(session)
    return {"message": "Excluded products"}