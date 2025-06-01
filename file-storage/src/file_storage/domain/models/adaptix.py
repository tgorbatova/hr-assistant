from adaptix import Retort, name_mapping

from file_storage.presentation.filters.model import MongoID, NestedMongoID

retort = Retort(
    recipe=[
        name_mapping(MongoID, map={"id": "_id"}),
        name_mapping(NestedMongoID, map={"oid": "$oid"}),
    ]
)
