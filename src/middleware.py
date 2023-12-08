"""
A module containing Middleware
"""
import logging
from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from nicegui import Client, app, ui
from starlette.responses import Response

# unrestricted_page_routes = {'/login'}
logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Diese Middleware beschränkt den Zugriff auf alle NiceGUI-Seiten.

    Sie leitet den Benutzer zur Anmeldeseite weiter, wenn er nicht authentifiziert ist.
    """

    async def dispatch(self, request: Request, call_next) -> RedirectResponse | Response:
        logger.info(f"{request.url.path.strip('/')=}")
        # logging.debug(f"{request.body()}")
        logger.info(f"{app.storage.user.get('authenticated', False)=}")

        not_auth = not app.storage.user.get("authenticated", False)
        not_login_signup = request.url.path.strip('/') not in ("login", "signup")
        flag = not_auth and not_login_signup
        logger.info(f"{flag=}")
        # The user is not authenticated and the path is not login / signup
        if flag:
            return RedirectResponse("/login")
        return await call_next(request)
