"""
A module containing Middleware
"""
import logging
from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from nicegui import app
from starlette.responses import Response

# unrestricted_page_routes = {'/login'}
logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    A middleware to check if the user is authenticated
    """

    async def dispatch(self, request: Request, call_next) -> RedirectResponse | Response:
        """Checks if the user is authenticated. If it's not, redirects to /login"""
        striped_request_url_path = request.url.path.strip('/')
        logger.info(f"{striped_request_url_path=}")
        logger.debug(f"{app.storage.user.get('authenticated', False)=}")
        not_auth = not app.storage.user.get("authenticated", False)
        # Avoid redirecting '_nicegui/1.3.18/static/fonts/flUhRq6tzZclQEJ-Vdg-IuiaDsNcIhQ8tQ.woff2'
        # or /login or /signup
        not_login_signup_nicegui = (
            '_nicegui' not in striped_request_url_path and
            striped_request_url_path not in ("login", "signup")
            )

        flag = not_auth and not_login_signup_nicegui
        logger.debug(f"{flag=}")
        # The user is not authenticated and the path is not login / signup
        if flag:
            # await asyncio.sleep(10)
            logger.info(f"redirecting")
            return RedirectResponse("/login")

        return await call_next(request)
