from dataclasses import replace
from typing import Any, Iterable, Optional, Sequence, cast

from mysql.connector import MySQLConnection, connect

from pydbio.commands import (
    gen_columns,
    gen_set,
    gen_table_name,
    gen_values,
    gen_where,
)
from pydbio.connection import SqlIO
from pydbio.helpers import extract_mysql_type
from pydbio.tablemeta import TableField, TableMetaData, min_max

from .configtypes import Config, ExecuteResult, QueryParams, QueryParamsIn


def open_mysql_connection_native(config: Config) -> MySQLConnection:
    con = connect(
        user=config.user,
        password=config.password,
        host=config.host,
        database=config.database,
        port=config.port,
        ssl_ca=config.ssl_ca,
        ssl_cert=config.ssl_cert,
        ssl_key=config.ssl_key,
        connection_timeout=100,
        use_pure=True,
    )

    return cast(MySQLConnection, con)


class MySQL(SqlIO):
    _quote_symbol = "`"

    _table_metadatas: dict[str, TableMetaData] = {}

    def __init__(self, config: Config):
        self.config = replace(config)
        self.conn = self._insternal_connect()

    def _insternal_connect(self) -> MySQLConnection:
        return open_mysql_connection_native(self.config)

    def _get_connection(self) -> MySQLConnection:
        try:
            if not self.conn.is_connected():
                self.conn = self._insternal_connect()

        except Exception:
            self.conn = self._insternal_connect()

        return self.conn

    def execute(self, query: str, params: QueryParams = ()) -> ExecuteResult:
        try:
            cur = self._get_connection().cursor(dictionary=False)
            cur.execute(query, params=params)
            if cur.with_rows:
                data = cur.fetchall()
                columns = list(cur.column_names)
            else:
                data = []
                columns = []

            return data, columns
        finally:
            cur.close()

    def executemany(self, query: str, params: Sequence[Any]):
        try:
            cur = self._get_connection().cursor(dictionary=False)
            cur.executemany(query, params)
        finally:
            cur.close()

    def commit(self):
        self._get_connection().commit()

    def rollback(self):
        self._get_connection().commit()

    def close(self):
        self._get_connection().close()

    def table_metadata(self, name: str) -> TableMetaData:
        if name in self._table_metadatas:
            return self._table_metadatas[name]

        self._table_metadatas[name] = read_table_metadata(name, self)
        return self._table_metadatas[name]

    def database(self) -> str:
        return self._get_connection().database

    def escape_string(self, value: str) -> str:
        con = self._get_connection()
        if con.converter is None:
            raise RuntimeError("mysql.con.converter is None")

        to_mysql = con.converter.to_mysql
        escape = con.converter.escape

        cvalue = to_mysql(value)  # type: ignore
        cvalue = escape(cvalue)
        # value = quote(value)

        return cast(str, cvalue.decode())  # type: ignore


def read_table_metadata(table_name: str, mysql: MySQL) -> TableMetaData:
    """reads table metadata

    Parameters
    ----------
    table_name: str,
    db_name: Optional[str], database name, if is None than use current database

    Returns
    -------
    TableMetaData object
    """

    name = mysql.escape_string(table_name)

    db_name = mysql.database()

    tmd = TableMetaData(name, db_name)

    data = mysql.fetch_dict(query=f"describe `{db_name}`.`{name}`")
    for r in data:
        field = TableField(name=r["Field"].lower())

        if "auto_increment" in r["Extra"] or "DEFAULT_GENERATED" in r["Extra"]:
            field.is_ai = True

        if r["Null"] == "NO" and r["Default"] is None:
            field.is_not_null = True

        field.is_uni = r["Key"] == "UNI"
        field.is_pk = r["Key"] == "PRI"

        ftype = r["Type"]
        if isinstance(ftype, bytes):
            ftype = ftype.decode("utf-8")

        field.field_type, field.size = extract_mysql_type(ftype)
        field.min_value, field.max_value = min_max(field.size)

        tmd.fields[field.name] = field

    data = mysql.fetch_dict(
        f"show index from `{name}` from `{db_name}` where non_unique = 0"
    )

    for r in data:
        field_name = r["Column_name"].lower()
        tmd.fields[field_name].is_uni = True

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

    if ignore:
        insert = "insert ignore"
    else:
        insert = "insert"

    return f"{insert} into {table_name}\n({columns})\nvalues({values})"


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
            f"{sep}{field}{sep}=vals.{sep}{field}{sep}"
            for field in fields
            if field not in unique_fields
        ]
    )
    if on_dupl == "":
        on_dupl = ",\n".join(
            [
                f"{sep}{field}{sep}=vals.{sep}{field}{sep}"
                for field in unique_fields
            ]
        )

    if ignore:
        insert = "insert ignore"
    else:
        insert = "insert"

    return f"""{insert} into {table_name}
({columns})
values({values}) as vals
on duplicate key update
{on_dupl}"""


def update_command(
    table_name: str,
    fields: Iterable[str],
    unique_fields: Iterable[str],
    dict_style: bool,
    sep: str,
    db_name: Optional[str] = None,
) -> str:
    table_name = gen_table_name(table_name=table_name, db_name=db_name, sep=sep)

    set_fields = [f for f in fields if f not in unique_fields]
    unique_fields = [f for f in fields if f in unique_fields]

    sets = gen_set(fields=set_fields, dict_style=dict_style, sep=sep)
    where = gen_where(fields=unique_fields, dict_style=dict_style, sep=sep)

    return f"""update {table_name}
set {sets}
where {where}"""


def replace_command(
    table_name: str,
    fields: Iterable[str],
    dict_style: bool,
    sep: str,
    db_name: Optional[str] = None,
):
    columns = gen_columns(fields=fields, sep=sep)
    values = gen_values(fields=fields, dict_style=dict_style)
    table_name = gen_table_name(table_name=table_name, db_name=db_name, sep=sep)

    return f"replace into {table_name} ({columns}) values ({values})"


def get_operand(if_op: str) -> str:
    if_op = if_op.lower()
    if if_op == "g":
        return ">"
    elif if_op == "l":
        return "<"
    elif if_op == "ge":
        return ">="
    elif if_op == "le":
        return "<="
    elif if_op == "e":
        return "="

    raise AssertionError("'if_op' = {'l', 'g', 'le', 'ge', 'e'}")


def insert_update_if_command(
    table_name: str,
    fields: Iterable[str],
    if_field: str,
    if_op: str,
    unique_fields: Iterable[str],
    dict_style: bool,
    sep: str,
    db_name: Optional[str] = None,
) -> str:
    columns = gen_columns(fields=fields, sep=sep)
    values = gen_values(fields=fields, dict_style=dict_style)
    table_name = gen_table_name(table_name=table_name, db_name=db_name, sep=sep)
    if_op = get_operand(if_op)

    on_dupl = ",\n".join(
        [
            f"{sep}{field}{sep}=if(vals.{sep}{if_field}{sep} {if_op} {table_name}.{sep}{if_field}{sep}, vals.{sep}{field}{sep}, {table_name}.{sep}{field}{sep})"
            for field in fields
            if field not in unique_fields
        ]
    )
    if on_dupl == "":
        on_dupl = ",\n".join(
            [
                f"{sep}{field}{sep}=vals.{sep}{field}{sep}"
                for field in unique_fields
            ]
        )

    return f"""insert into {table_name}
            ({columns})
            values({values}) as vals
            on duplicate key update
            {on_dupl}"""
