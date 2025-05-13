from typing import NewType

from front.utils.client import BaseHttpClient

FilesRequestClient = NewType("FilesRequestClient", BaseHttpClient)
