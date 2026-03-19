from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union


class Dialects(str, Enum):
    mysql = "mysql"
    psql = "psql"


@dataclass
class Config:
    user: str
    database: str
    password: str
    host: str
    port: int
    dialect: Dialects
    ssl_ca: Optional[str] = None
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None


QueryParams = Union[Dict[str, Any], Sequence[Any]]
QueryParamsIn = Sequence[Any]

QueryResult = Sequence[Any]
QueryColumns = Sequence[str]
ExecuteResult = Tuple[QueryResult, QueryColumns]
