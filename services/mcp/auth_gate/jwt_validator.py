from http.cookies import CookieError, SimpleCookie

import jwt

from utils.logger import logger


def extract_user_from_cookie(cookie_header: str, access_secret: str, refresh_secret: str) -> str | None:
    jar: SimpleCookie = SimpleCookie()
    try:
        jar.load(cookie_header)
    except CookieError as error:
        logger.warning(f"Rejected malformed cookie header error={error}")
        return None

    candidates: list[tuple[str, str]] = []
    if refresh_secret and "refreshToken" in jar:
        candidates.append((jar["refreshToken"].value, refresh_secret))
    if access_secret and "token" in jar:
        candidates.append((jar["token"].value, access_secret))

    for token_value, secret in candidates:
        try:
            payload = jwt.decode(token_value, secret, algorithms=["HS256"], options={"require": ["exp"]})
        except jwt.PyJWTError:
            continue

        user_id = payload.get("id") or payload.get("sub")
        if user_id is not None:
            return str(user_id)

    return None
