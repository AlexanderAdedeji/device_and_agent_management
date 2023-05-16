from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from sqlalchemy.exc import IntegrityError

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session
from commonlib.models import Base as BaseDeclarativeClass


ModelType = TypeVar("ModelType", bound=BaseDeclarativeClass)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class Base(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        """
        Base Object with methods to Create, Read, Update, Delete (CRUD) for any model .

        **Parameters**

        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def get_multi_by_ids(self, db: Session, *, ids: List[int]) -> List[ModelType]:
        in_condition = self.model.id.in_(ids)
        return db.query(self.model).filter(in_condition)

    def get_all(self, db: Session) -> List[ModelType]:
        return db.query(self.model).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)  # type: ignore
        db.add(db_obj)
        try:
            db.commit()
            db.refresh(db_obj)
        except IntegrityError as e:
            e.add_detail("an error occured while trying to create " + str(e.params))
            raise e
        return db_obj

    def get_by_field(
        self, db: Session, *, field_name: str, field_value: str
    ) -> ModelType:
        return (
            db.query(self.model)
            .filter(getattr(self.model, field_name) == field_value)
            .first()
        )

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        try:
            db.commit()
            db.refresh(db_obj)
        except IntegrityError as e:
            e.add_detail("An error occured while trying to update " + str(e.params))
            raise e
        return db_obj

    def remove(self, db: Session, *, id: int) -> ModelType:
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj
