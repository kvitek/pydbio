import os
from typing import Tuple

from pydbio.connection import SqlIO
from pydbio.myio import MySQL
from pydbio.pgio import PSQL

from .configtypes import Config, Dialects

__CONFIGS: dict[Tuple[str, int], SqlIO] = {}


def configure(configs: dict[str, Config]):
    pid = os.getpid()

    for name, config in configs.items():
        if config.dialect == Dialects.psql:
            __CONFIGS[(name.lower(), pid)] = PSQL(config)
        elif config.dialect == Dialects.mysql:
            __CONFIGS[(name.lower(), pid)] = MySQL(config)


def get_connection(name: str) -> SqlIO:
    pid = os.getpid()
    p = __CONFIGS.get((name.lower(), pid))
    if p is None:
        raise KeyError(f"no config for name `{name}`")

    return p
