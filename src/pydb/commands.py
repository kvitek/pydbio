from typing import Iterable, Optional


def generate(fields: Iterable[str], conjunction: str, dict_style: bool) -> str:
    if dict_style:
        return conjunction.join([f"%({f})s" for f in fields])

    return conjunction.join([f"%s" for f in fields])


def gen_values(fields: Iterable[str], dict_style: bool) -> str:
    return generate(fields, ", ", dict_style)


def gen_where(fields: Iterable[str], dict_style: bool, sep: str) -> str:
    if dict_style:
        return " and ".join([f"{sep}{f}{sep} = %({f})s" for f in fields])

    return " and ".join([f"{sep}{f}{sep} = %s" for f in fields])


def gen_columns(fields: Iterable[str], sep: str) -> str:
    return ", ".join(f"{sep}{f}{sep}" for f in fields)


def gen_set(fields: Iterable[str], dict_style: bool, sep: str) -> str:
    if dict_style:
        return ", ".join(
            [f"{sep}{field}{sep} = %({field})s" for field in fields]
        )

    return ", ".join([f"{sep}{field}{sep} = %s" for field in fields])


def gen_table_name(
    table_name: str, *, db_name: Optional[str] = None, sep: str
) -> str:
    if db_name is None:
        return f"{sep}{table_name}{sep}"

    return f"{sep}{db_name}{sep}.{sep}{table_name}{sep}"
