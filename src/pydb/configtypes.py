from enum import Enum
from typing import Any, Dict, Optional, Sequence, Tuple, Union

from pydantic import BaseModel


class Dialects(str, Enum):
    mysql = "mysql"
    psql = "psql"


class Config(BaseModel):
    user: str
    database: str
    password: str
    host: str
    port: int
    dialect: Dialects
    search_path: Optional[list[str]] = None
    ssl_ca: Optional[str] = None
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None


QueryParams = Union[Dict[str, Any], Sequence[Any]]
QueryParamsIn = Sequence[Any]

QueryResult = list[Tuple[Any, ...]]
QueryColumns = Sequence[str]
ExecuteResult = Tuple[QueryResult, QueryColumns]
