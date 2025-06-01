import typing
from typing import Annotated, Generic, TypeVar

from fastapi import Depends, Query
from pydantic import Field
from pydantic.json_schema import SkipJsonSchema

T = TypeVar("T")
ModelT = TypeVar("ModelT")

if typing.TYPE_CHECKING:
    FromQuery = Annotated[T, ...]
    OptionalField = Annotated[T | None, ...]
else:

    class FromQuery(Generic[T]):
        def __class_getitem__(cls, item: T) -> T:
            return Annotated[item, Depends()]

    class OptionalField(Generic[T]):
        def __class_getitem__(cls, item: T) -> T | None:
            # TODO: найти способ передавать описание
            return Annotated[item | SkipJsonSchema[None], Field(Query(None))]
