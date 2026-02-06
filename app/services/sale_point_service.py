from models.model import SalePoints
from schemas.schema import SalePointResponseDTO

async def create_sale_point(name: str, email: str, password: str, session):
    sale_point = session.query(SalePoints).filter(SalePoints.name == name).first()

    if(sale_point):
        return "Ja existe"
    sale_point = SalePoints(name, email, password)
    session.add(sale_point)
    session.commit()

    return SalePointResponseDTO.model_validate(sale_point)

async def get_sale_point(id: int, session):
    sale_point = session.query(SalePoints).filter(SalePoints.id == id).first()

    if(sale_point):
        return SalePointResponseDTO.model_validate(sale_point)
    
async def get_all_sales_points(session):
    sales_points = session.query(SalePoints).all()

    return [SalePointResponseDTO.model_validate(sp) for sp in sales_points]

def fake_hash_password(password: str):
    return "azmpfwyuvc" + password