import enum
from collections.abc import Generator, Iterable
from typing import Any

from bson import ObjectId
from fastapi import Query
from motor.motor_asyncio import AsyncIOMotorCursor
from pydantic import BaseModel, Field, ValidationError, model_validator

OPERATORS_MAP = {
    "ne": "$ne",
    "lt": "$lt",
    "lte": "$lte",
    "gt": "$gt",
    "gte": "$gte",
    "in": "$in",
    "nin": "$nin",
}


class OrderDirection(enum.StrEnum):
    ASC = "asc"
    DESC = "desc"


class BaseMotorFilter(BaseModel):
    """Базовый фильтр для Mongo."""

    _TECHNICAL_FIELDS: set[str]

    @model_validator(mode="after")  # type: ignore[misc]
    def validate_fields(self) -> None:
        for field_name, _ in self.filtering_fields:
            if field_name.count("__") not in {0, 1}:
                raise ValidationError(
                    "You should use separator once in filter field name. Example: field_name__operator"
                )

    @property
    def filtering_fields(self) -> Generator[tuple[str, Any]]:
        fields = self.model_dump(exclude_none=True, exclude_unset=True)
        return ((field_name, value) for field_name, value in fields.items() if field_name not in self._TECHNICAL_FIELDS)

    def compile(self) -> dict[str, dict[str, Any]]:
        """Compiles filters to apply inside 'result' field of MongoDB documents."""
        compiled_filters: dict[str, Any] = {}

        for filter_field, value in self.filtering_fields:
            if "__" in filter_field:
                field_path, operator = filter_field.rsplit("__", 1)
            else:
                field_path, operator = filter_field, "eq"

            if operator not in OPERATORS_MAP and operator != "eq":
                raise ValidationError(f"Operator {operator} is not supported")

            # Special case: _id field (which was 'id')
            if field_path == "id":
                mongo_field = "_id"
                value = self._compile_id(value)
            else:
                # All other fields go under 'result.'
                mongo_field = f"result.{field_path.replace('__', '.')}"  # dot-notation path

            compiled_filters[mongo_field] = value if operator == "eq" else {OPERATORS_MAP[operator]: value}

        return compiled_filters

    def _compile_id(self, identifiers: str | Iterable[str]) -> ObjectId | Iterable[ObjectId]:
        if isinstance(identifiers, Iterable):
            return tuple(ObjectId(identifier) for identifier in identifiers)
        return ObjectId(identifiers)


class _MotorSortFilter(BaseMotorFilter):
    """Фильтр сортировки для Mongo."""

    order_by: str = Field(Query("_id", description="Поле для сортировки"))
    order_direction: OrderDirection = Field(Query(OrderDirection.ASC, description="Направление сортировки"))

    def _sort(self, cursor: AsyncIOMotorCursor) -> AsyncIOMotorCursor:
        if self.order_direction == OrderDirection.DESC:
            return cursor.sort([(self.order_by, -1)])
        return cursor.sort([(self.order_by, 1)])
