from dataclasses import Field
from typing import Any, ClassVar, Protocol, TypeVar, Union


class DataclassInstance(Protocol):
    __dataclass_fields__: ClassVar[dict[str, Field[Any]]]


from pydantic import BaseModel

T_BASE = TypeVar("T_BASE", bound=BaseModel)
T_DATA = TypeVar("T_DATA", bound=DataclassInstance)
T_BASE_DATA = TypeVar("T_BASE_DATA", bound=Union[BaseModel, DataclassInstance])
