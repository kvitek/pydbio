import decimal
from dataclasses import dataclass, field
from typing import Dict, Set, Tuple


def min_max(size: Tuple[int, ...]) -> Tuple[decimal.Decimal, decimal.Decimal]:
    if len(size) != 2:
        return (decimal.Decimal(0), decimal.Decimal(0))

    v = decimal.Decimal(10) ** (size[0] - size[1] - 1) - 1

    return (-v, v)


@dataclass
class TableField:
    name: str
    is_ai: bool = False
    is_pk: bool = False
    is_uni: bool = False
    is_not_null: bool = False
    field_type: str = "varchar"
    size: Tuple[int, ...] = ()
    min_value: decimal.Decimal = decimal.Decimal(0)
    max_value: decimal.Decimal = decimal.Decimal(0)


@dataclass
class TableMetaData:
    name: str
    db_name: str
    fields: Dict[str, TableField] = field(default_factory=dict)

    @property
    def primary(self) -> Set[str]:
        return set([f.name for f in self.fields.values() if f.is_pk])
