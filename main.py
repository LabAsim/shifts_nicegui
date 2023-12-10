#!/usr/bin/env python3
"""This is just a very simple authentication example.

Please see the `OAuth2 example at FastAPI <https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/>`_  or
use the great `Authlib package <https://docs.authlib.org/en/v0.13/client/starlette.html#using-fastapi>`_ to implement a classing real authentication system.
Here we just demonstrate the NiceGUI integration.
"""
import asyncio
import functools
import inspect
import logging
import os
import threading
import time
from asyncio import AbstractEventLoop
from nicegui import (
    app,
    ui
)
from starlette.responses import RedirectResponse
from fastapi import Request

from src.db.funcs import connect
from src.formatter import color_logging
from src.helpers import (
    log_func_name,
    func_name,
    check_letters_password,
    check_letters_username
)
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


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.debug(f"{request}>{process_time=}")
    return response


def force_sync(fn):
    '''
    turn an async function to sync function
    '''
    import asyncio

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        res = fn(*args, **kwargs)
        if asyncio.iscoroutine(res):
            logger.info("it's a coroutine")
            loop = asyncio.get_event_loop()
            task = loop.create_task(res())
            return task
        return res

    return wrapper


@ui.page("/show")
async def show():
    ui.label("Hello, FastAPI!")

    # NOTE dark mode will be persistent for each user across tabs and server restarts
    ui.dark_mode().bind_value(app.storage.user, "dark_mode")
    ui.checkbox("dark mode").bind_value(app.storage.user, "dark_mode")


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


async def try_signup(_username: str, _password: str) -> bool:
    log_func_name(
        thelogger=logger, fun_name=func_name(inspect.currentframe())
    )
    logger.debug(f"{_username=}, {_password=}")
    if len(_password) > 8 and len(_username) > 8:
        await connect(password=_password, username=_username)
        passwords[_username] = _password
        logger.debug("saved")
        # app.storage.user["signup_thread_flag"] = True
        return True
    else:
        logger.warning(f"Password and/or username is <8 characters")
        # app.storage.user["signup_thread_flag"] = True
        return False


from nicegui.background_tasks import create


def handle_signup_click(event) -> None:
    log_func_name(
        thelogger=logger, fun_name=func_name(inspect.currentframe())
    )
    # logger.info(f"{a.args=}")
    # logger.info(f"{password_value=}")
    # logger.info(f"{username_value=}")
    _loop = asyncio.get_event_loop()
    us = app.storage.user.get("username_value")
    pa = app.storage.user.get("password_value")
    logger.info(f"{us=}")
    logger.info(f"{pa=}")

    def run_thread(loop: AbstractEventLoop, a: str, b: str):
        pass

    def run_try_signup_in_thread(loop: AbstractEventLoop, a: str, b: str) -> bool:
        """
        See https://www.slingacademy.com/article/python-add-a-coroutine-to-an-already-running-event-loop/
        """
        log_func_name(
            thelogger=logger, fun_name=func_name(inspect.currentframe())
        )
        # Submit the coroutine to the loop
        _future = asyncio.run_coroutine_threadsafe(try_signup(a, b), loop=loop)

        # Wait for the result
        print(f"Result: {_future.result()}")
        ui.open("/show")
        return _future.result()

    # The thread works but it cannot redirect the user to /show
    logger.info(f"{app.storage.user=}")
    app.storage.user["signup_thread_flag"] = False
    thread = threading.Thread(target=run_try_signup_in_thread, args=(_loop, us, pa))
    thread.start()
    # while not app.storage.user["signup_thread_flag"]:
    #     #logger.info(f"{app.storage.user['signup_thread_flag']}")
    #     pass
    # else:
    # time.sleep(10)
    # Join blocks everything
    # thr_result = thread.join()
    # logger.info(f"{thr_result=}")
    # with concurrent.futures.ThreadPoolExecutor() as executor:
    #     future = executor.submit(run_try_signup_in_thread, _loop, us, pa)
    #     return_value = future.result()
    #     logger.info(f"{return_value=}")
    #     if return_value:
    logger.info(f"")
    if app.storage.user.get("signup_thread_flag"):
        ui.open("/show")
        logger.debug("opening /show")
    # pfunc = functools.partial(try_signup, _username=us, _password=pa)
    # pfunc = force_sync(pfunc)
    # pfunc()
    logger.info(" endded")


@ui.page("/signup")
async def signup() -> None:
    log_func_name(
        thelogger=logger, fun_name=func_name(inspect.currentframe())
    )

    with ui.card().classes("right-center"):
        ui.label("Welcome!")

        username = ui.input(
            label="Username",
            validation={
                'Input too short': lambda value: len(value) > 8,
                'Input too long': lambda value: len(value) < 30,
                'English letters and numbers only': lambda value: check_letters_username(value)
            },
        ).bind_value_to(
            app.storage.user,
            'username_value'
        ).props('clearable')  # .tooltip(text="English letters and numbers only")

        password = ui.input(
            "Password",
            password=True,
            password_toggle_button=True,
            validation={
                'Input too short': lambda value: len(value) > 8,
                'Input too long': lambda value: len(value) < 30,
                'Not allowed characters. '
                'Allowed characters: A-Z,a-z,1-9,_!@#$%^&*': lambda value: check_letters_password(value),
            },
        ).bind_value_to(
            app.storage.user,
            'password_value'
        ).props('clearable')  # .tooltip(text="Allowed characters: A-Z,a-z,1-9,_!@#$%^&*")
        # Currently, it does not work as intended.
        #
        #     .on(
        #     "keydown.enter", handle_signup_click
        # )

        # Check this for async button
        # https://nicegui.io/documentation/button#await_button_click
        b = ui.button(
            text="Sign up?",
            on_click=lambda event: try_signup(_username=username.value, _password=password.value)
        ).on(
            "keydown.enter", handler=handle_signup_click
        )


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        storage_secret="THIS_NEEDS_TO_BE_CHANGED",
        title="Shifts allocator",
        reload='FLY_ALLOC_ID' not in os.environ,
    )
