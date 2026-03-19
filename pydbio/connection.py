from abc import ABC, abstractmethod
from typing import Any, Dict, List, Sequence

from pydbio.configtypes import (
    Config,
    ExecuteResult,
    QueryParams,
    QueryParamsIn,
    QueryResult,
)
from pydbio.helpers import parse_dict_command, parse_positional_command
from pydbio.tablemeta import TableMetaData


class DatabaseConnection(ABC):
    def __init__(self, config: Config) -> None: ...

    @abstractmethod
    def execute(
        self, query: str, params: QueryParams = ()
    ) -> ExecuteResult: ...

    @abstractmethod
    def executemany(self, query: str, params: Sequence[Any]): ...

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


class SqlIO(DatabaseConnection):
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

    def fetch_tuples(self, query: str, params: QueryParams = ()) -> QueryResult:
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
