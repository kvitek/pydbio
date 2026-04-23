import sys
import warnings
from abc import ABC, abstractmethod
from dataclasses import MISSING, fields, is_dataclass
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Literal,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeAlias,
    overload,
)

from pydantic import BaseModel

from .configtypes import (
    Config,
    ExecuteResult,
    QueryParams,
    QueryParamsIn,
    QueryResult,
)
from .helpers import (
    check_sequence,
    data_to_tuples,
    extract_columns,
    parse_dict_command,
    parse_positional_command,
)
from .tablemeta import TableMetaData
from .types import DATA_TYPE, T_BASE, T_BASE_DATA, T_DATA
from .where import WhereParams, gen_header, gen_where


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

    @abstractmethod
    def insert_update(
        self, data: DATA_TYPE, table_name: str, columns: Sequence[str] = ()
    ): ...

    @classmethod
    @abstractmethod
    def quote(cls, text: str) -> str: ...

    @abstractmethod
    def _table_metadata(self, table_name: str) -> TableMetaData: ...

    @abstractmethod
    def _insert_update_cmd(
        self,
        table_name: str,
        fields: Iterable[str],
        unique_fields: Iterable[str],
        dict_style: bool,
        sep: str,
        ignore: bool,
        db_name: Optional[str] = None,
    ) -> str: ...


_TABLE_META: dict[int, dict[str, TableMetaData]] = {}


class SqlIO(DatabaseConnection):
    _quote_symbol: str = ""

    InitParams: TypeAlias = WhereParams

    def table_metadata(self, name: str) -> TableMetaData:
        conid = id(self)
        global _TABLE_META

        conn_meta = _TABLE_META.setdefault(conid, {})
        meta = conn_meta.get(name)
        if meta is not None:
            return meta

        conn_meta[name] = self._table_metadata(name)

        return conn_meta[name]

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

    @overload
    def fetch_typed(
        self,
        klass: Type[T_DATA],
        query: str,
        params: QueryParams = (),
    ) -> list[T_DATA]: ...
    @overload
    def fetch_typed(
        self,
        klass: Type[T_BASE],
        query: str,
        params: QueryParams = (),
    ) -> list[T_BASE]: ...

    def fetch_typed(
        self,
        klass: Type[T_DATA] | Type[T_BASE],
        query: str,
        params: QueryParams = (),
    ) -> list[T_DATA] | list[T_BASE]:
        if issubclass(klass, BaseModel):
            return self._fetch_typed_pydantic(klass, query=query, params=params)  # type: ignore
        else:
            return self._fetch_typed_dataclass(
                klass, query=query, params=params
            )

    def _fetch_typed_dataclass(
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

    def _fetch_typed_pydantic(
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

    def header_string(
        self,
        klass: type[T_BASE_DATA],
        *,
        table: str | None = None,
        all: bool = False,
        exclude: Sequence[str] = (),
    ) -> str:
        columns = self.header(klass, all=all, exclude=exclude)

        if table is None:
            return ", ".join((self.quote(c) for c in columns))
        else:
            return ", ".join(
                (f"{self.quote(table)}.{self.quote(c)}" for c in columns)
            )

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
    ) -> list[T_BASE]: ...
    @overload
    def find_all(
        self,
        klass: type[T_DATA],
        table: str,
        where: InitParams,
        *,
        all: bool = True,
        exclude: Sequence[str] = (),
    ) -> list[T_DATA]: ...

    def find_all(
        self,
        klass: type[T_DATA] | type[T_BASE],
        table: str,
        where: InitParams,
        *,
        all: bool = True,
        exclude: Sequence[str] = (),
    ) -> list[T_DATA] | list[T_BASE]:
        columns = self.header(klass, all=all, exclude=exclude)
        header = ", ".join((self.quote(c) for c in columns))
        params, wh = self.where(where)

        query = f"select {header} from {self.quote(table)}"
        if wh:
            query += f" where {wh}"

        return self.fetch_typed(klass=klass, query=query, params=params)  # type: ignore

    @overload
    def fetch_all(
        self,
        klass: type[T_BASE],
        query: str,
        where: InitParams,
    ) -> list[T_BASE]: ...
    @overload
    def fetch_all(
        self,
        klass: type[T_DATA],
        query: str,
        where: InitParams,
    ) -> list[T_DATA]: ...

    def fetch_all(
        self,
        klass: type[T_DATA] | type[T_BASE],
        query: str,
        where: InitParams,
    ) -> list[T_BASE] | list[T_DATA]:
        params, wh = self.where(where)

        if wh:
            query += f" where {wh}"

        return self.fetch_typed(klass=klass, query=query, params=params)  # type: ignore

    def insert_update(
        self, data: DATA_TYPE, table_name: str, columns: Sequence[str] = ()
    ):
        if not data:
            return

        meta = self.table_metadata(table_name)

        fields = list(meta.fields)
        mandatory = meta.mandatory()

        if not columns:
            columns = fields

        columns = check_sequence(
            data[0], columns=columns, mandatory=mandatory, fields=fields
        )

        if isinstance(data[0], dict):
            dict_style = True
            new_data = data
        else:
            dict_style = False
            new_data = data_to_tuples(data, columns=columns)

        cmd = self._insert_update_cmd(
            table_name=table_name,
            dict_style=dict_style,
            fields=columns,
            unique_fields=meta.primary,
            ignore=False,
            sep=self._quote_symbol,
        )

        self.executemany(query=cmd, data=new_data)
