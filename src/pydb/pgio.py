from __future__ import annotations

from typing import Any, Iterable, Optional, Sequence, cast

from psycopg import InterfaceError, InternalError

from pydb.types import DATA_TYPE, ClassInstance

from .commands import gen_columns, gen_table_name, gen_values
from .helpers import data_to_tuples, extract_psql_size, extract_psql_type
from .tablemeta import TableField, TableMetaData, min_max

try:
    import psycopg.sql as sql
    from psycopg import Connection as PSQLConnection
    from psycopg import OperationalError, connect
    from psycopg.errors import InFailedSqlTransaction, OperationalError
    from psycopg_pool import ConnectionPool

    # from psycopg.pool import ThreadedConnectionPool
except ImportError:
    raise RuntimeError("install psycopg library")

from .configtypes import Config, ExecuteResult, QueryParams
from .connection import SqlIO
from .helpers import retry

failed_connection_retry = retry(
    2,
    (OperationalError, InternalError, InterfaceError),
    SqlIO,
)


def open_psql_connection_native(
    host: str, port: int, database: str, user: str, passwd: str
) -> PSQLConnection:
    return connect(
        dbname=database, user=user, password=passwd, host=host, port=port
    )


class PSQL(SqlIO):
    _quote_symbol = '"'

    def __init__(self, config: Config) -> None:
        self.config = config.model_copy()
        self.conn = self._insternal_connect()

    def _insternal_connect(self) -> PSQLConnection:
        conn = open_psql_connection_native(
            host=self.config.host,
            port=self.config.port,
            database=self.config.database,
            user=self.config.user,
            passwd=self.config.password,
        )

        if self.config.search_path:
            query = sql.SQL("SET search_path = {}").format(
                sql.SQL(",").join(map(sql.Identifier, self.config.search_path))
            )
            conn.execute(query)
            conn.commit()

        return conn

    def _get_connection(self) -> PSQLConnection:
        try:
            if self.conn.closed != 0:
                self.conn = self._insternal_connect()
        except OperationalError as oe:
            self.conn = self._insternal_connect()

        return self.conn

    @failed_connection_retry
    def execute(self, query: str, params: QueryParams = ()) -> ExecuteResult:
        with self._get_connection().cursor() as cur:
            cur.execute(cast(Any, query), params)
            data = []
            if cur.rownumber is not None:
                for c in cur.results():
                    data.extend(c.fetchall())

            if cur.description:
                columns = [c[0] for c in cur.description]
            else:
                columns = []

        return data, columns

    @failed_connection_retry
    def executemany(self, query: str, data: Sequence[Any]):
        with self._get_connection().cursor() as cur:
            cur.executemany(cast(Any, query), data)

    @failed_connection_retry
    def commit(self):
        self._get_connection().commit()

    @failed_connection_retry
    def rollback(self):
        self._get_connection().rollback()

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass

    def _table_metadata(self, name: str) -> TableMetaData:
        return read_table_metadata(name, self)

    def database(self) -> str:
        return cast(str, self.fetch_tuples("select current_schema()")[0][0])

    @failed_connection_retry
    def copy_from(
        self,
        data: Iterable[Sequence[Any]],
        columns: Iterable[str],
        table_name: str,
    ):
        # new_data_str = Converter.data_to_str(data, "\t")
        qry = sql.SQL("COPY {} ({}) FROM STDIN").format(
            sql.Identifier(table_name),
            sql.SQL(",").join(map(sql.Identifier, columns)),
        )

        with self._get_connection().cursor() as cur:
            with cur.copy(qry) as copy:
                for row in data:
                    copy.write_row(row)

    def copy_from_class(
        self,
        data: Sequence[ClassInstance] | Sequence[Sequence[Any]],
        table_name: str,
    ):
        if not data:
            return

        meta = self.table_metadata(table_name)
        columns = list(meta.fields)
        data_columns = list(data[0].__dict__)
        columns = list(set(columns).intersection(data_columns))

        new_data = data_to_tuples(data=data, columns=columns)

        self.copy_from(data=new_data, columns=columns, table_name=table_name)

    def _insert_update_cmd(
        self,
        table_name: str,
        fields: Iterable[str],
        unique_fields: Iterable[str],
        dict_style: bool,
        sep: str,
        ignore: bool,
        db_name: str | None = None,
    ) -> str:
        return insert_update_command(
            table_name=table_name,
            fields=fields,
            unique_fields=unique_fields,
            dict_style=dict_style,
            sep=sep,
            ignore=ignore,
            db_name=db_name,
        )


def read_table_metadata(table_name: str, psql: PSQL) -> TableMetaData:
    """reads table metadata

    Parameters
    ----------
    table_name: str,

    Returns
    -------
    TableMetaData object
    """

    tmd = TableMetaData(table_name, psql.database())

    data = psql.fetch_dict(
        "select * from information_schema.columns where table_name = %s",
        (tmd.name,),
    )

    for r in data:
        field = TableField(name=r["column_name"])

        if r["is_nullable"] == "NO":
            field.is_not_null = True
        if r["column_default"] is not None:
            field.default_value = r["column_default"].split("::")[0].strip("'")

        field.field_type = extract_psql_type(r)
        field.size = extract_psql_size(r)
        if field.field_type == "decimal":
            field.min_value, field.max_value = min_max(field.size)

        tmd.fields[field.name] = field

    data = psql.fetch_tuples(
        """
            SELECT a.attname, format_type(a.atttypid, a.atttypmod) AS data_type
            FROM   pg_index i
            JOIN   pg_attribute a ON a.attrelid = i.indrelid
                                AND a.attnum = ANY(i.indkey)
            WHERE  i.indrelid = %s::regclass
            AND    i.indisprimary;""",
        (tmd.name,),
    )

    for r in data:
        tmd.fields[r[0]].is_pk = True
        tmd.fields[r[0]].is_uni = True

    return tmd


def insert_command(
    table_name: str,
    fields: Iterable[str],
    dict_style: bool,
    sep: str,
    ignore: bool,
    db_name: Optional[str] = None,
) -> str:
    columns = gen_columns(fields=fields, sep=sep)
    values = gen_values(fields=fields, dict_style=dict_style)
    table_name = gen_table_name(table_name=table_name, db_name=db_name, sep=sep)

    on_conflict = ""
    if ignore:
        on_conflict = "on conflict do nothing"

    return (
        f"insert into {table_name}\n({columns})\nvalues({values}) {on_conflict}"
    )


def insert_update_command(
    table_name: str,
    fields: Iterable[str],
    unique_fields: Iterable[str],
    dict_style: bool,
    sep: str,
    ignore: bool,
    db_name: Optional[str] = None,
) -> str:
    columns = gen_columns(fields=fields, sep=sep)
    values = gen_values(fields, dict_style)
    table_name = gen_table_name(table_name=table_name, db_name=db_name, sep=sep)

    on_dupl = ",\n".join(
        [
            f"{sep}{field}{sep} = EXCLUDED.{sep}{field}{sep}"
            for field in fields
            if field not in unique_fields
        ]
    )
    if on_dupl == "":
        on_dupl = ",\n".join(
            [
                f"{sep}{field}{sep} = EXCLUDED.{sep}{field}{sep}"
                for field in unique_fields
            ]
        )

    insert = "insert"

    return f"""{insert} into {table_name}
({columns})
values({values})
on conflict ({','.join(f for f in unique_fields)})
do update set
{on_dupl}"""
