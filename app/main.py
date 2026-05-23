from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from app.core.config import settings
from app.core.route_class import StandardAPIRoute
from app.api.v1 import api_router


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description="FastAPI layered architecture backend project setup",
        version="0.1.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Set custom route class for global response wrapping
    app.router.route_class = StandardAPIRoute

    # Set up CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Adjust for production as needed
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global Exception Handlers
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "status": exc.status_code,
                "error": exc.detail
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "status": 422,
                "error": jsonable_encoder(exc.errors())
            }
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "status": 500,
                "error": str(exc) or "Internal Server Error"
            }
        )

    # Healthcheck endpoint
    @app.get("/health", tags=["health"])
    async def health_check():
        return {
            "status": "healthy",
            "app_name": settings.APP_NAME,
            "environment": settings.ENVIRONMENT,
        }

    # Register API routers
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_app()
