from resume_service.di.providers.app import AppProvider
from resume_service.di.providers.client import InfrastructureProvider

base_providers = (AppProvider(), InfrastructureProvider())
