from fastapi import FastAPI
from routes.auth_routes import auth_router

app = FastAPI()
app.include_router(auth_router)