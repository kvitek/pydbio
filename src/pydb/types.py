from dataclasses import Field
from typing import (
    Any,
    ClassVar,
    Mapping,
    Protocol,
    Sequence,
    TypeVar,
    Union,
    runtime_checkable,
)


@runtime_checkable
class DataclassInstance(Protocol):
    __dataclass_fields__: ClassVar[dict[str, Field[Any]]]


@runtime_checkable
class ClassInstance(Protocol):
    __dict__: dict[str, Any]


from pydantic import BaseModel

T_BASE = TypeVar("T_BASE", bound=BaseModel)
T_DATA = TypeVar("T_DATA", bound=DataclassInstance)
T_BASE_DATA = TypeVar("T_BASE_DATA", bound=Union[BaseModel, DataclassInstance])

DATA_TYPE_MAPPING = Sequence[dict[str, Any]]
DATA_TYPE_SEQ_MODEL_CLASS = (
    Sequence[Sequence[Any]]
    | Sequence[DataclassInstance]
    | Sequence[BaseModel]
    | Sequence[ClassInstance]
)
DATA_TYPE = DATA_TYPE_SEQ_MODEL_CLASS | DATA_TYPE_MAPPING
DATA_TYPE_ROW = (
    dict[str, Any]
    | Sequence[Any]
    | DataclassInstance
    | BaseModel
    | ClassInstance
)
