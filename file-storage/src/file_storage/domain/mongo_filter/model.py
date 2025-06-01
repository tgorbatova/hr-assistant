from typing import Generic

from pydantic import BaseModel

from file_storage.domain.mongo_filter.types import ModelT


class Paginated(BaseModel, Generic[ModelT]):
    page: int
    page_size: int
    total_pages: int
    total_docs: int

    items: list[ModelT]
