import sys
import warnings
from abc import ABC, abstractmethod
from dataclasses import MISSING, fields, is_dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Literal,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    overload,
)

from pydantic import BaseModel

from pydbio.configtypes import (
    Config,
    ExecuteResult,
    QueryParams,
    QueryParamsIn,
    QueryResult,
)
from pydbio.helpers import parse_dict_command, parse_positional_command
from pydbio.tablemeta import TableMetaData
from pydbio.types import T_BASE, T_BASE_DATA, T_DATA, DataclassInstance
from pydbio.where import InitParams, gen_header, gen_where


class DatabaseConnection(ABC):
    def __init__(self, config: Config) -> None: ...

    @abstractmethod
    def execute(
        self, query: str, params: QueryParams = ()
    ) -> ExecuteResult: ...

    @abstractmethod
    def executemany(self, query: str, data: Sequence[Any]): ...

    @abstractmethod
    def commit(self): ...

    @abstractmethod
    def rollback(self): ...

    # @abstractmethod
    # def start_transaction(self): ...

    @abstractmethod
    def close(self): ...

    @abstractmethod
    def table_metadata(self, name: str) -> TableMetaData: ...

    @classmethod
    @abstractmethod
    def quote(cls, text: str) -> str: ...


class SqlIO(DatabaseConnection):
    _quote_symbol: str = ""

    @classmethod
    def quote(cls, text: str) -> str:
        elems = text.split(".")

        return ".".join(
            (f"{cls._quote_symbol}{e}{cls._quote_symbol}" for e in elems)
        )

    def execute_in(
        self,
        query: str,
        *,
        params: QueryParams = (),
        params_in: QueryParamsIn = (),
    ) -> ExecuteResult:
        if isinstance(params, dict):
            query, params = parse_dict_command(query, params, params_in)
        else:
            query, params = parse_positional_command(query, params, params_in)

        return self.execute(query, params)

    @overload
    def fetch_tuples(
        self,
        query: str,
        params: QueryParams,
        columns: Literal[True],
    ) -> ExecuteResult: ...

    @overload
    def fetch_tuples(
        self,
        query: str,
        params: QueryParams,
        columns: Literal[False],
    ) -> QueryResult: ...

    @overload
    def fetch_tuples(
        self,
        query: str,
        params: QueryParams,
    ) -> QueryResult: ...

    @overload
    def fetch_tuples(
        self,
        query: str,
        params: QueryParams = (),
    ) -> QueryResult: ...

    def fetch_tuples(
        self,
        query: str,
        params: QueryParams = (),
        columns=False,
    ) -> QueryResult | ExecuteResult:
        if columns:
            return self.execute(query=query, params=params)
        else:
            res, _ = self.execute(query=query, params=params)
        return res

    def fetch_dict(
        self, query: str, params: QueryParams = ()
    ) -> List[Dict[str, Any]]:
        res, columns = self.execute(query=query, params=params)
        return [dict(zip(columns, row)) for row in res]

    def fetch_tuples_in(
        self,
        query: str,
        *,
        params: QueryParams = (),
        params_in: QueryParamsIn = (),
    ) -> QueryResult:
        res, _ = self.execute_in(
            query=query, params=params, params_in=params_in
        )
        return res

    def fetch_dict_in(
        self,
        query: str,
        *,
        params: QueryParams = (),
        params_in: QueryParamsIn = (),
    ) -> List[Dict[str, Any]]:
        res, columns = self.execute_in(
            query=query, params=params, params_in=params_in
        )
        return [dict(zip(columns, row)) for row in res]

    def fetch_typed(
        self,
        klass: Type[T_DATA],
        query: str,
        params: QueryParams = (),
    ) -> list[T_DATA]:
        data, columns = self.fetch_tuples(
            query=query, params=params, columns=True
        )
        if not data:
            return []

        # if "__dataclass_fields__" not in dir(klass):
        if not is_dataclass(klass):
            raise AttributeError("`klass` must be dataclass")

        class_fields = fields(klass)
        names = [f.name for f in class_fields]
        required = [f.name for f in class_fields if f.default is MISSING]

        if names == columns or required == columns:
            return [klass(*r) for r in data]

        diff = set(required).difference(columns)
        if diff:
            raise RuntimeError(
                f"annotations `{', '.join(diff)}` for class `{klass.__name__}` doesn't exist on query `{query}`"
            )

        gettrace = getattr(sys, "gettrace", None)
        if gettrace is not None and gettrace():
            warnings.warn(
                f"it would be slightly faster if you order columns in `{query}` to match columns in {klass.__name__}",
                RuntimeWarning,
            )

        res = []
        for r in data:
            params = dict(zip(columns, r))
            res.append(klass(**params))
        return res

    def fetch_typed_pydantic(
        self,
        klass: Type[T_BASE],
        query: str,
        params: QueryParams = (),
    ) -> list[T_BASE]:
        data, columns = self.fetch_tuples(
            query=query, params=params, columns=True
        )
        if not issubclass(klass, BaseModel):
            raise AttributeError("`klass` must be subclass of BaseModel")

        required = [
            name for name, f in klass.model_fields.items() if f.is_required()
        ]

        diff = set(required).difference(columns)
        if diff:
            raise RuntimeError(
                f"annotations `{', '.join(diff)}` for class `{klass.__name__}` doesn't exist on query `{query}`"
            )

        res = []
        for r in data:
            params = dict(zip(columns, r))
            res.append(klass.model_validate(params))
        return res

    @staticmethod
    def header(
        klass: type[T_BASE_DATA],
        *,
        all: bool = False,
        exclude: Sequence[str] = (),
    ) -> list[str]:
        return gen_header(klass, all=all, exclude=exclude)

    @staticmethod
    def where(params: InitParams) -> Tuple[list[Any], str]:
        return gen_where(params=params)

    @overload
    def find_all(
        self,
        klass: type[T_BASE],
        table: str,
        where: InitParams,
        *,
        all: bool = True,
        exclude: Sequence[str] = (),
    ) -> Sequence[T_BASE]: ...
    @overload
    def find_all(
        self,
        klass: type[T_DATA],
        table: str,
        where: InitParams,
        *,
        all: bool = True,
        exclude: Sequence[str] = (),
    ) -> Sequence[T_DATA]: ...

    def find_all(
        self,
        klass: type[T_DATA] | type[T_BASE],
        table: str,
        where: InitParams,
        *,
        all: bool = True,
        exclude: Sequence[str] = (),
    ) -> Sequence[T_BASE] | Sequence[T_DATA]:
        columns = self.header(klass, all=all, exclude=exclude)
        header = ", ".join((self.quote(c) for c in columns))
        params, wh = self.where(where)

        query = f"select {header} from {self.quote(table)}"
        if wh:
            query += f" where {wh}"

        if issubclass(klass, BaseModel):
            return self.fetch_typed_pydantic(klass, query=query, params=params)  # type: ignore
        else:
            return self.fetch_typed(klass, query=query, params=params)
