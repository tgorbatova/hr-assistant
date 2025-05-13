from dishka import make_async_container

from front.main.config import Settings, settings
from front.main.di.providers.app import AppProvider
from front.main.di.providers.client import ClientProvider
from front.main.di.providers.repository import RepositoryProvider

providers = (AppProvider(), ClientProvider(), RepositoryProvider())

container = make_async_container(
    *providers,
    context={Settings: settings},
)
