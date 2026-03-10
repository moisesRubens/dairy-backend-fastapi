from fastapi import APIRouter

outbound_router = APIRouter(prefix="/outbounds", tags=["Outbounds"])

@outbound_router.patch("/{id}")
async def edit_outbound():
    pass