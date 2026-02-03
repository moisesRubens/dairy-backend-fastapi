from fastapi import APIRouter

auth_router = APIRouter(prefix="/auth", tags=["Auth"])

@auth_router.post("/logout")
async def logout():
    return {"message": "logout"}

@auth_router.post("/login")
async def login():
    return {"message": "login"}