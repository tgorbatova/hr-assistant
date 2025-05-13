from dishka import Provider, Scope, WithParents, provide_all, AnyOf, provide

from resume_service.infrastructure.adapters.file import FilesRepository

from resume_service.domain.types.clients import FilesRequestClient
from resume_service.main.config import settings
from resume_service.utils.client import BaseHttpClient


class InfrastructureProvider(Provider):
    scope = Scope.APP

    request_dependencies = provide_all(
        WithParents[FilesRepository],
        scope=Scope.REQUEST,
    )

    @provide
    async def files_client(self) -> AnyOf[FilesRequestClient, BaseHttpClient]:
        return BaseHttpClient(
            base_url=str(settings.INFRA.CLIENT.FILES.BASE_URL).rstrip("/") + settings.INFRA.CLIENT.FILES.DOMAIN
        )
