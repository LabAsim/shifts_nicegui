#!/usr/bin/env python3
"""This is just a very simple authentication example.

Please see the `OAuth2 example at FastAPI <https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/>`_  or
use the great `Authlib package <https://docs.authlib.org/en/v0.13/client/starlette.html#using-fastapi>`_ to implement a classing real authentication system.
Here we just demonstrate the NiceGUI integration.
"""
import functools
import logging
import os
import time
from typing import Callable

from nicegui import app, ui
from starlette.responses import RedirectResponse
from fastapi import Request

from src.formatter import color_logging
from src.middleware import AuthMiddleware

# from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
# app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(AuthMiddleware)

logger = logging.getLogger(__name__)
console = color_logging(level=logging.DEBUG)
logging.basicConfig(
    level=logging.DEBUG,
    force=True,
    handlers=[console],
)  # Force is needed here to re config logging

# in reality users passwords would obviously need to be hashed

passwords = {"user1": "pass1", "user2": "pass2", "user3": "pass3", "1": "1"}

valid_users = dict()
valid_profiles = dict()
pending_users = dict()
discussion_posts = dict()
request_headers = dict()
cookies = dict()


async def check_auth(func: Callable) -> Callable:

    @functools.wraps(func)
    async def inner_func(*args, **kwargs) -> RedirectResponse:
        logger.debug("Plain decorator")
        if not app.storage.user.get("authenticated", False):
            logger.warning("redirect")
            return RedirectResponse("/login")
        logger.info("calling func")
        return await func(*args, **kwargs)

    return inner_func


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.debug(f"{request}>{process_time=}")
    return response


@ui.page("/show")
async def show():
    ui.label("Hello, FastAPI!")

    # NOTE dark mode will be persistent for each user across tabs and server restarts
    ui.dark_mode().bind_value(app.storage.user, "dark_mode")
    ui.checkbox("dark mode").bind_value(app.storage.user, "dark_mode")


#@check_auth
@ui.page("/")
async def main_page() -> None | RedirectResponse:
    if not app.storage.user.get("authenticated", False):
        return RedirectResponse("/login")
    with ui.column().classes("absolute-top"):
        ui.chat_message(
            'Hello NiceGUI!',
            name='Robot',
            stamp='now',
            avatar='https://robohash.org/ui'
        )
    with ui.column().classes("absolute-center items-center"):
        ui.label(f'Hello {app.storage.user["username"]}!').classes("text-2xl")
        ui.button(
            on_click=lambda: (app.storage.user.clear(), ui.open("/login")), icon="logout"
        ).props("outline round")


@ui.page("/login")
async def login() -> None | RedirectResponse:
    async def try_login() -> None:  # local function to avoid passing username and password as arguments
        if passwords.get(username.value) == password.value:
            app.storage.user.update(
                {
                    "username": username.value,
                    "authenticated": True
                }
            )
            ui.open("/")
        else:
            ui.notify(
                message="Wrong username or password",
                color="negative"
            )

    if app.storage.user.get("authenticated", False):
        return RedirectResponse("/")
    with ui.card().classes("absolute-center"):
        username = ui.input("Username").on("keydown.enter", try_login)
        password = ui.input("Password", password=True, password_toggle_button=True).on(
            "keydown.enter", try_login
        )
        ui.button(text="Log in", on_click=try_login)
        ui.button(
            text="Sign up",
            on_click=lambda: (
                ui.open("/signup")
            ),
            # lambda : (ui.open('/signup'), signup(username=username.value, password=password.value))
        )


@ui.page("/signup")
async def signup() -> None:
    def try_signup(username: str, password: str) -> None:
        logger.debug(f"{username=}, {password=}")
        if not passwords.get(username):
            passwords[username] = password
            logger.debug("saved")
            ui.open("/show")
            logger.debug("opening /show")

    with ui.card().classes("right-center"):
        ui.label("Hello, FastAPI!")
        username = ui.input("Username").on("keydown.enter", try_signup)
        password = ui.input("Password", password=True, password_toggle_button=True).on(
            "keydown.enter", try_signup
        )
        ui.button(
            text="Sign up?",
            on_click=lambda: (
                try_signup(username=username.value, password=password.value),
            ),
        )


if __name__ == "__main__":
    ui.run(
        storage_secret="THIS_NEEDS_TO_BE_CHANGED",
        title="Shifts allocator",
        reload='FLY_ALLOC_ID' not in os.environ,
    )
