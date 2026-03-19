import re
import time
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from pydbio._const import PSQL_MYSQL_DATA_TYPES

T = TypeVar("T")


def retry(
    retry: int, exc_cls: Tuple[Type[Exception], ...], delay: float = 0.1
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    if retry <= 0:
        raise AttributeError()

    def decorator(function: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args, **kwargs) -> T:
            current = Exception()

            for i in range(retry + 1):
                try:
                    return function(*args, **kwargs)
                except exc_cls as e:
                    time.sleep(delay)
                    current = e

            raise current

        return wrapper

    return decorator


POSITIONAL_ARGS = re.compile(r"\%s", re.I)
DICTIONARY_ARGS = re.compile(r"\%\((\w+)\)s")


def parse_positional_command(
    query: str, params: Sequence[Any], params_in: Sequence[Any]
) -> Tuple[str, Sequence[Any]]:
    if "(__in__)" not in query:
        return query, params

    if len(params_in) == 0:
        return query, params

    part_one, _ = query.split("(__in__)")
    pos_args_in_one = len(POSITIONAL_ARGS.findall(part_one))

    template = ",".join("%s" for _ in range(len(params_in)))
    query = query.replace("__in__", template)

    return query, (
        list(params[:pos_args_in_one])
        + list(params_in)
        + list(params[pos_args_in_one:])
    )


def parse_dict_command(
    query: str, params: Dict[str, Any], params_in: Sequence[Any]
) -> Tuple[str, Sequence[Any]]:

    parts = query.split("(__in__)")

    new_params = []
    new_parts = []
    for i, part in enumerate(parts):
        pos = 0
        while s := DICTIONARY_ARGS.search(part, pos):
            _, pos = s.span()
            name = s.group(1)
            new_params.append(params[name])

        new_parts.append(DICTIONARY_ARGS.sub("%s", part))

        if i == 0 and len(parts) == 2:
            new_params += params_in

    pattern = ",".join(["%s"] * len(params_in))
    query = f"({pattern})".join(new_parts)

    return query, new_params


def cast_enum(value: Any) -> Any:
    if isinstance(value, str):
        return str(value)
    elif isinstance(value, int):
        return int(value)

    return value


def cast_enums(
    params: Iterable[Any],
) -> Union[Sequence[Any], Dict[str, Any]]:
    if isinstance(params, dict):
        return {k: cast_enum(v) for k, v in params.items()}

    return [cast_enum(v) for v in params]


def extract_psql_size(r: Dict[str, Any]) -> Tuple[int, ...]:
    size: List[int] = []

    names = ["character_maximum_length", "numeric_precision", "numeric_scale"]
    for name in names:
        if r[name] is not None:
            size.append(int(r[name]))

    return tuple(size)


def extract_psql_type(r: Dict[str, Any]) -> str:
    return PSQL_MYSQL_DATA_TYPES.get(r["data_type"], r["data_type"])


TYPES = re.compile(r"(\w+)\s*(\((\d+(\,\d)?)\))?", re.IGNORECASE)


def extract_mysql_type(ftype: str) -> Tuple[str, Tuple[int, ...]]:
    groups = TYPES.findall(ftype)
    try:
        field_type = groups[0][0]
        size: Tuple[int, ...] = ()
        if groups[0][2]:
            size_list = groups[0][2].split(",")
            if len(size_list) == 2:
                size = (int(size_list[0]), int(size_list[1]))
            else:
                size = (int(size_list[0]),)

        return field_type, size
    except IndexError:
        raise Exception(f'unsupported field type "{ftype}"')
