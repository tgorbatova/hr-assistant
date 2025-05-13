from typing import NewType

from resume_service.utils.client import BaseHttpClient

FilesRequestClient = NewType("FilesRequestClient", BaseHttpClient)
