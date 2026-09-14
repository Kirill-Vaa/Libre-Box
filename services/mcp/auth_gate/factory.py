from fastapi import FastAPI

from auth_gate.routes import build_auth_router


def create_auth_app(access_secret: str, refresh_secret: str) -> FastAPI:
    application = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    application.include_router(build_auth_router(access_secret, refresh_secret))
    return application
