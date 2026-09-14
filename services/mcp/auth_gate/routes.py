from fastapi import APIRouter, Request, Response

from auth_gate.jwt_validator import extract_user_from_cookie


def build_auth_router(access_secret: str, refresh_secret: str) -> APIRouter:
    router = APIRouter()

    @router.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @router.get("/auth/validate")
    async def validate(request: Request) -> Response:
        cookie_header = request.headers.get("cookie", "")
        user_id = extract_user_from_cookie(cookie_header, access_secret, refresh_secret)
        if user_id is None:
            return Response(status_code=401)

        return Response(headers={"X-Auth-User": user_id})

    return router
