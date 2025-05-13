from dishka import Provider, Scope, from_context, provide
from starlette.websockets import WebSocket

from front.main.config import (
    AppSettings,
    ClientSettings,
    InfrastructureSettings,
    Settings,
)


class AppProvider(Provider):
    scope = Scope.APP

    settings = from_context(Settings)
    socket = from_context(WebSocket)

    @provide
    def app_settings(self, settings: Settings) -> AppSettings:
        return settings.APP

    @provide
    def infra_settings(self, settings: Settings) -> InfrastructureSettings:
        return settings.INFRA

    @provide
    def client_settings(self, settings: InfrastructureSettings) -> ClientSettings:
        return settings.CLIENT
