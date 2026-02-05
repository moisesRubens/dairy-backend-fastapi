from models.model import db
from sqlalchemy.orm import sessionmaker

async def make_session():
    try:
        Session = sessionmaker(bind=db)
        session = Session()
        yield session
    finally:
        session.close()