from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NestedMongoID:
    oid: str


@dataclass(frozen=True, slots=True)
class MongoID:
    id: NestedMongoID


@dataclass(frozen=True, slots=True)
class ExperienceInfo:
    position: str
    company: str
    location: str | None
    period: str
    responsibilities: list[str]


@dataclass(frozen=True, slots=True)
class EducationInfo:
    degree: str | None
    major: str | None
    institution: str | None
    location: str | None
    period: str | None


@dataclass(frozen=True, slots=True)
class ContactInfo:
    phone: list[str] | None
    email: list[str] | None
    other: list[str] | None


@dataclass(frozen=True, slots=True)
class PersonalInfo:
    age: int | None
    birth_date: str | None
    location: str | None


@dataclass(frozen=True, slots=True)
class MongoResume:
    _id: str
    file_id: str
    name: str
    personal_info: PersonalInfo
    contact_info: ContactInfo
    skills: list[str]
    experience: list[ExperienceInfo]
    education: list[EducationInfo]
    courses: list[str] | None
    languages: list[str] | None
    other: dict | None
