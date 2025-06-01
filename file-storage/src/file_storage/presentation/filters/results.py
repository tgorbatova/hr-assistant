from file_storage.domain.mongo_filter.paginator import MotorPaginator
from file_storage.domain.mongo_filter.types import OptionalField
from file_storage.presentation.filters.model import MongoResume


class ResumeResultsFilter(MotorPaginator[MongoResume]):
    _model = MongoResume

    # ID
    id: OptionalField[str]
    id__in: OptionalField[list[str]]

    # Имя кандидата
    name: OptionalField[str]
    name__in: OptionalField[list[str]]

    # Локация
    personal_info__location: OptionalField[str]
    personal_info__location__in: OptionalField[list[str]]

    # Возраст
    personal_info__age: OptionalField[int]
    personal_info__age__gte: OptionalField[int]
    personal_info__age__lte: OptionalField[int]

    # Навыки
    skills: OptionalField[str]
    skills__in: OptionalField[list[str]]

    # Языки
    languages: OptionalField[str]
    languages__in: OptionalField[list[str]]

    # Образование (университеты, степени и т.п.)
    education__institution: OptionalField[str]
    education__institution__in: OptionalField[list[str]]

    education__degree: OptionalField[str]
    education__degree__in: OptionalField[list[str]]

    # Опыт работы (компании, должности и др.)
    experience__company: OptionalField[str]
    experience__company__in: OptionalField[list[str]]

    experience__position: OptionalField[str]
    experience__position__in: OptionalField[list[str]]

    class Constants(MotorPaginator.Constants):
        DEFAULT_PAGE_SIZE = 20
