from models.model import Product
from schemas.schema import ProductResponseDTO
from exceptions.ProductExceptions import ExistingProductException, ProductNotFound

def get_all_products_service(session):
    products = session.query(Product).all()
    if not products:
        raise Exception("Empty storage")
    result = []
    for product in products:
        product_data = ProductResponseDTO.model_validate(product)
        result.append(product_data)
    return result

def delete_product_service(session, id):
    product = session.get(Product, id)
    if not product:
        raise ProductNotFound()
    product_data = ProductResponseDTO.model_validate(product)
    session.delete(product)
    session.commit() 
    return product_data

def create_product_service(name, price, amount, kg, liters, session):
    if exist_product(name, session):
        raise ExistingProductException()
    product = Product()
    product.name = name
    product.price = price
    product.amount = amount
    product.kg = kg
    product.liters = liters
    session.add(product)
    session.commit()
    
    return ProductResponseDTO.model_validate(product)

def exist_product(name, session):
    product = session.query(Product).filter(Product.name==name).first()
    return True if product else False