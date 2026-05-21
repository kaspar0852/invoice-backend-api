from fastapi import APIRouter
from app.core.route_class import StandardAPIRoute
from app.api.v1.routes.users import router as users_router
from app.api.v1.routes.customers_route import router as customers_router

api_router = APIRouter(route_class=StandardAPIRoute)
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(customers_router, prefix="/customers", tags=["customers"])
