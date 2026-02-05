from models.model import Product

async def get_all_products(session):
    products = session.query(Product).all()
    
    result = []
    
    for product in products:
        items = session.query(Product).filter_by(id=product.id).first()
        result.append({
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "amount": product.amount,
            "kg": product.kg,
            "liters": product.liters
        })
        
    return result