import uuid
from typing import NewType

FileId = NewType("FileId", uuid.UUID)
FolderId = NewType("FolderId", uuid.UUID)
