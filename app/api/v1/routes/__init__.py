from app.api.v1.routes.users import router as users_router
from app.api.v1.routes.customers_route import router as customers_router
from app.api.v1.routes.dashboard_route import router as dashboard_router

__all__ = ["users_router", "customers_router", "dashboard_router"]
