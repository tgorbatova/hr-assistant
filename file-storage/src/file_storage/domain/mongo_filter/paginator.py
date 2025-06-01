from collections.abc import Callable
from math import ceil
from typing import Any, Generic

from fastapi import Query
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorCursor
from pydantic import Field

from file_storage.domain.mongo_filter.base import _MotorSortFilter
from file_storage.domain.mongo_filter.model import Paginated
from file_storage.domain.mongo_filter.types import ModelT


class MotorPaginator(_MotorSortFilter, Generic[ModelT]):
    """Фильтр пагинации для Mongo.

    Для использования методов execute_one и execute необходимо указать атрибут _model.
    Для переопределения атрибутов по умолчанию необходимо создать вложенный класс Constants(MotorPaginator.Constants)
    и переопределить нужные.
    """

    class Constants:
        """Константы по умолчанию для пагинации."""

        DEFAULT_FIRST_PAGE: int = 1
        DEFAULT_PAGE_SIZE: int = 20
        DEFAULT_USE_PAGINATION: bool = True

    _model: type[ModelT]
    _TECHNICAL_FIELDS = {
        "page",
        "page_size",
        "total_pages",
        "total_docs",
        "use_pagination",
        "order_by",
        "order_direction",
    }

    page: int = Field(Query(Constants.DEFAULT_FIRST_PAGE, description="Номер страницы"), ge=1)
    page_size: int = Field(Query(Constants.DEFAULT_PAGE_SIZE, description="Количество элементов на странице"), ge=1)

    use_pagination: bool = Field(
        Query(
            Constants.DEFAULT_USE_PAGINATION,
            description="Использовать пагинацию. Если false, то вернутся все документы.",
        )
    )

    def paginate(self, cursor: AsyncIOMotorCursor) -> AsyncIOMotorCursor:
        cursor = self._sort(cursor)
        if not self.use_pagination:
            return cursor
        return cursor.skip((self.page - 1) * self.page_size).limit(self.page_size)

    def find(self, collection: AsyncIOMotorCollection) -> AsyncIOMotorCursor:
        """Метод запроса к коллекции, компилирующий фильтр, сортировку и пагинацию.

        :param collection: Коллекция для поиска документов.
        :return: Курсор, по которому можно итерироваться.
        """
        return self.paginate(collection.find(self.compile()))

    async def execute_one(self) -> ModelT:
        """Получение отфильтрованного DTO документа."""
        # TODO: implement
        raise NotImplementedError

    async def execute(
        self,
        collection: AsyncIOMotorCollection,
        loader: Callable[[Any, type[list[ModelT]]], ModelT] | None = None,
    ) -> Paginated[ModelT]:
        """Получение отфильтрованных DTO документов с пагинацией.

        :param collection:
        :param loader: Retort.load
        :return:
        """
        assert hasattr(self, "_model"), "Model type must be set"

        total_docs = await collection.count_documents(self.compile())

        raw_docs = await self.find(collection).to_list(None)
        loaded_data = []
        for doc in raw_docs:
            doc["_id"] = str(doc["_id"])  # convert ObjectId if needed
            # flatten result into top level
            if "result" in doc:
                doc.update(doc.pop("result"))
            loaded_data.append(doc)

        page_size = len(loaded_data)

        return Paginated(
            page=self.page,
            page_size=page_size,
            total_pages=ceil(total_docs / page_size) if page_size > 0 else 0,
            total_docs=total_docs,
            items=(
                loader(loaded_data, list[self._model])  # type: ignore[name-defined]
                if loader is not None
                else [self._model(**item) for item in loaded_data]
            ),
        )
