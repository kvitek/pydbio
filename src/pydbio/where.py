from __future__ import annotations

import datetime as dt
from dataclasses import MISSING, fields, is_dataclass
from decimal import Decimal
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    get_args,
)

from pydbio.types import T_BASE_DATA

if TYPE_CHECKING:
    from _typeshed import DataclassInstance

from pydantic import BaseModel

OpType = Literal["=", "!=", "like", "<", "<=", ">", ">=", "is", "is not"]
OpTypeKeys = set(get_args(OpType))

LogicalOp = Literal["and", "or", "not"]
LogicalOpKeys = set(get_args(LogicalOp))

DataType = Union[int, str, bool, float, Decimal, dt.date, dt.datetime, None]

Param = Union[
    Tuple[OpType, DataType],
    DataType,
    Tuple[Literal["in"], Sequence[DataType]],
]

ParamOp = Union[Param, dict[str, "ParamOp"]]


# InitParams = dict[str, dict[str, ParamOp]]
InitParams = dict[str, ParamOp]


def convert_logical(name: LogicalOp, value: ParamOp, subs: list[Any]) -> str:
    if not isinstance(value, dict):
        raise RuntimeError(f"logical value of `{name} `must be dict")
    where_list = get_params_where(value, subs)
    if len(where_list) == 0:
        return ""

    if name == "not":
        if len(where_list) > 1:
            raise RuntimeError(
                f"`not` directive must contain only one directive"
            )
        return f"not ({where_list[0]})"
    else:
        return f" {name} ".join(f"({w})" for w in where_list)


def get_params_where(params: dict[str, ParamOp], subs: list[Any]) -> list[str]:
    where: list[str] = []
    for name, value in params.items():
        if name in LogicalOpKeys:
            logical = convert_logical(cast(LogicalOp, name), value, subs)
            if logical != "":
                where.append(logical)
        else:
            if isinstance(value, dict):
                raise RuntimeError(f"param value must by tuple or value")

            if not isinstance(value, tuple):
                if value is not None:
                    where.append(f"{name} = %s")
                    subs.append(value)
            else:
                if value[0] in OpTypeKeys:
                    if value[0] in ("is", "is not") or value[1] is not None:
                        where.append(f"{name} {value[0]} %s")
                        subs.append(value[1])
                elif value[0] == "in":
                    if value[1]:
                        where.append(
                            f"{name} in ({','.join(['%s']*len(value[1]))})"
                        )
                    subs.extend(value[1])
                else:
                    raise RuntimeError(f"unknown opernd `{name}`")

    return where


def gen_where(params: InitParams) -> Tuple[list[Any], str]:
    """
    Returns
    -------
        tuple (params, where string)

    Args:
        params: InitParams
        example:
        ```
            {
                "and": {
                    "cik": 1000,
                    "sic": ["in", (100, 200)]
                }
            }
        ```
    """

    subs: list[Any] = []
    where = []
    where.extend(get_params_where(params, subs))

    return subs, " and ".join((f"({w})" for w in where))


def gen_header(
    klass: Type[T_BASE_DATA], *, all: bool = False, exclude: Sequence[str] = ()
) -> list[str]:
    if is_dataclass(klass):
        cf = fields(klass)
        if all:
            names = [f.name for f in cf]
        else:
            names = [f.name for f in cf if f.default is MISSING]

    elif issubclass(klass, BaseModel):
        if all:
            names = [name for name in klass.model_fields]
        else:
            names = [
                name
                for name, f in klass.model_fields.items()
                if f.is_required()
            ]
    else:
        raise AttributeError(
            "`klass` must be dataclass or subclass of BaseModel"
        )

    return list(filter(lambda x: x not in exclude, names))
