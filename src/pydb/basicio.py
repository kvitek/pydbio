import os
from typing import Tuple

from .configtypes import Config, Dialects
from .connection import SqlIO
from .myio import MySQL
from .pgio import PSQL

__CONFIGS: dict[Tuple[str, int], SqlIO] = {}


def configure(configs: dict[str, Config]):
    pid = os.getpid()
    global __CONFIGS

    for name, config in configs.items():
        name = name.lower()
        if (name, pid) in __CONFIGS:
            return __CONFIGS[(name, pid)]

        if config.dialect == Dialects.psql:
            __CONFIGS[(name, pid)] = PSQL(config)
        elif config.dialect == Dialects.mysql:
            __CONFIGS[(name, pid)] = MySQL(config)
        else:
            raise AttributeError(f"wrong dialect `{config.dialect}`")


def configure_close():
    global __CONFIGS
    for conn in __CONFIGS.values():
        try:
            conn.close()
        except Exception:
            pass

    __CONFIGS = {}


def get_connection(name: str) -> SqlIO:
    pid = os.getpid()
    p = __CONFIGS.get((name.lower(), pid))
    if p is None:
        raise KeyError(f"no config for name `{name}`")

    return p
