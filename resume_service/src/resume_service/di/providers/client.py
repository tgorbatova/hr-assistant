from dishka import AnyOf, Provider, Scope, WithParents, provide, provide_all
from openai import AsyncOpenAI

from resume_service.domain.types.clients import FilesRequestClient
from resume_service.infrastructure.adapters.file import FilesRepository
from resume_service.infrastructure.adapters.llm import LLMAdapter
from resume_service.main.config import settings
from resume_service.utils.client import BaseHttpClient


class InfrastructureProvider(Provider):
    scope = Scope.APP

    request_dependencies = provide_all(
        WithParents[FilesRepository],
        LLMAdapter,
        scope=Scope.REQUEST,
    )

    @provide
    async def files_client(self) -> AnyOf[FilesRequestClient, BaseHttpClient]:
        return BaseHttpClient(
            base_url=str(settings.INFRA.CLIENT.FILES.BASE_URL).rstrip("/") + settings.INFRA.CLIENT.FILES.DOMAIN
        )

    @provide
    async def llm_client(
        self,
    ) -> AsyncOpenAI:
        return AsyncOpenAI(
            api_key=settings.INFRA.CLIENT.LLM.TOKEN,
            base_url=settings.INFRA.CLIENT.LLM.URL,
        )
