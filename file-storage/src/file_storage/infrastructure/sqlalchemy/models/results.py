from sqlalchemy import Enum as PgEnum
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from file_storage.domain.models.file import FileId
from file_storage.domain.models.result import ResultId, ResultType
from file_storage.infrastructure.sqlalchemy.base import Base


class Results(Base):
    """Результаты."""

    __tablename__ = "results"

    id: Mapped[ResultId] = mapped_column(primary_key=True, index=True)
    file_id: Mapped[FileId] = mapped_column(ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    file_name: Mapped[str]
    folder_name: Mapped[str]
    path: Mapped[str]
    size: Mapped[int]
    type: Mapped[ResultType] = mapped_column(
        PgEnum(ResultType, name="result_type_enum", schema="files_schema"), nullable=False
    )

    __table_args__ = (UniqueConstraint("type", "file_id", name="uq_result_type_file_id"),)
