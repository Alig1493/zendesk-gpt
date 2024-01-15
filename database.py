import asyncio
import os
import traceback
from asyncio import Future, get_running_loop
from dataclasses import dataclass
from typing import List, Any, Dict

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import IndexModel
from pymongo.errors import OperationFailure, CollectionInvalid
from pymongo.results import UpdateResult, InsertManyResult, InsertOneResult


@dataclass
class MongoDB:
    _mongodb_uri: str = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

    def __post_init__(self):
        self._client = AsyncIOMotorClient(self._mongodb_uri)
        self._db = self._client["GPTTest"]

    def set_mongo_ids(self, documents: List[Dict[str, Any]]) -> None:
        for document in documents:
            if "id" in document:
                document["_id"] = document["id"] if isinstance(document["id"], ObjectId) else ObjectId(document["id"])
                del document["id"]

    async def validate_collection(self, collection_name: str):
        print(id(get_running_loop()))
        print("Checking if collection exists")
        try:
            # Try to validate a collection
            await self._db.validate_collection(collection_name)
        except OperationFailure as operational_failure:  # If the collection doesn't exist
            print(f"{collection_name} collection doesn't exist")
            raise operational_failure
        except TimeoutError as timeout_error:
            print(traceback.format_exc())
            raise timeout_error

    async def create_collection(self, collection_name: str):
        try:
            await self._db.create_collection(collection_name)
        except CollectionInvalid as invalid_collection_error:
            if "already exists" in str(invalid_collection_error):
                return
            raise invalid_collection_error

    async def get_collection(self, collection_name: str):
        await self.validate_collection(collection_name)
        return self._db[collection_name]

    async def create_indexes(self, collection_name: str, index_keys: List[str]):
        indexes = [IndexModel([index_key]) for index_key in index_keys]
        return self._db.get_collection(collection_name).create_indexes(indexes)

    async def insert_documents(self, collection_name: str, documents: List[Dict[str, Any]]) -> InsertManyResult:
        self.set_mongo_ids(documents)
        collection = await self.get_collection(collection_name)
        result = await collection.insert_many(documents)
        return result

    async def insert_document(self, collection_name: str, **document: Dict[str, Any]) -> InsertOneResult:
        self.set_mongo_ids([document])
        collection = await self.get_collection(collection_name)
        result = await collection.insert_one(document)
        return result

    async def find(
        self,
        collection_name: str,
        query: dict,
        exclude_fields: tuple = (),
        find_one: bool = False,
        sort: list = None
    ) -> list | Future:
        collection = await self.get_collection(collection_name)
        fields = {field: False for field in exclude_fields}
        match find_one:
            case True:
                return collection.find_one(query, fields or None, sort=sort)
            case False:
                return [
                    document async for document in collection.find(query, fields or None, sort=sort)
                ]

    async def update(self, collection_name: str, query: dict, data: dict, upsert: bool = False) -> None | UpdateResult:
        collection = await self.get_collection(collection_name)
        return collection.update_one(
            query,
            {"$set": data},
            upsert=upsert,
        )
