from pydantic import BaseModel


class ExperienceInfo(BaseModel):
    position: str
    company: str
    location: str | None = None
    period: str
    responsibilities: list[str]


class EducationInfo(BaseModel):
    degree: str | None = None
    major: str | None = None
    institution: str | None = None
    location: str | None = None
    period: str | None = None


class ContactInfo(BaseModel):
    phone: list[str] | None = None
    email: list[str] | None = None
    other: list[str] | None = None


class PersonalInfo(BaseModel):
    age: int | None = None
    birth_date: str | None = None
    location: str | None = None


class ResumeInfo(BaseModel):
    name: str
    personal_info: PersonalInfo
    contact_info: ContactInfo
    skills: list[str]
    experience: list[ExperienceInfo]
    education: list[EducationInfo]
    courses: list[str] | None = None
    languages: list[str] | None = None
    other: dict | None = None
