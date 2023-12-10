import asyncio
import dataclasses
import inspect
import logging
import os
import re
from functools import wraps, partial
from typing import Callable, Coroutine


@dataclasses.dataclass
class EnvVars:
    DBPASS = os.environ.get("asdadas")


def wrap_as_async(func) -> Callable:
    """Wraps a sync functions as an async one"""
    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs) -> Coroutine:
        if loop is None:
            loop = asyncio.get_event_loop()
        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)

    return run


def func_name(frame) -> str:
    """Returns the name of the function passed"""
    return inspect.getframeinfo(frame)[2]


def log_func_name(thelogger: logging.getLogger, fun_name: str) -> None:
    """Logs the name of the function"""
    thelogger.info(
        f"\t{fun_name}() called\n"
    )


def check_letters_username(string: str) -> bool:
    pattern = "^[A-Za-z0-9]+$"
    return bool(re.match(pattern=pattern, string=string))


def check_letters_password(string: str) -> bool:
    pattern = "^[A-Za-z0-9_!@#$%^&*]+$"
    return bool(re.match(pattern=pattern, string=string))

