from typing import Generic, Type, TypeVar, List
from bson.objectid import ObjectId
from pydantic.main import BaseModel
from pymongo.cursor import Cursor
from pymongo.database import Database
from pymongo.collection import Collection

from db.models.log import Base

ModelType = TypeVar("ModelType", bound=Base)


class Base(Generic[ModelType]):
    def __init__(self, db: Database, model: Type[ModelType]):
        self.model = model
        self.collection = db.get_collection(model.__collectionname__())

    def get_multiple(self, *, conditions={}) -> Cursor:
        return self.collection.find(conditions)

    def get(self, *, object_id: str) -> ModelType:
        document = self.collection.find_one({"_id": ObjectId(object_id)})
        return self.model(**document)

    def create(self, *, obj_in: ModelType) -> ObjectId:
        obj_in_dict = obj_in.dict()
        return self.collection.insert_one(obj_in_dict).inserted_id
