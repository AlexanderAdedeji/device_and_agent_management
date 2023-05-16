from backend.app.schemas.api_key import APIKeyCreate, UnsafeAPIKey
from backend.app.services import security
from backend.app.models import APIKey
from backend.app.db.repositories.base import Base
from sqlalchemy.orm import Session

from typing import List


class APIKeyRepository(Base[APIKey]):
    def mark_as_active(self, db: Session, api_key_obj: APIKey) -> APIKey:
        api_key_obj.is_active = True
        return self.update(db, db_obj=api_key_obj, obj_in={})

    def mark_as_inactive(self, db: Session, api_key_obj: APIKey) -> APIKey:
        api_key_obj.is_active = False
        return self.update(db, db_obj=api_key_obj, obj_in={})

    def get_all_with_user_id(self, db: Session, user_id: int) -> List[APIKey]:
        return db.query(APIKey).filter(APIKey.user_id == user_id).all()

    def verify_api_key(self, db: Session, *, plain_api_key: str) -> bool:
        hashed_api_key = security.get_api_key_hash(plain_api_key)
        api_key_obj = self.get_by_field(
            db, field_name="hashed_key", field_value=hashed_api_key
        )
        return api_key_obj and api_key_obj.is_active

    def create(self, db: Session, *, api_key_obj: APIKeyCreate) -> UnsafeAPIKey:
        plain_api_key = APIKey.generate_key()

        api_key_obj = api_key_obj.dict()
        api_key_obj["hashed_key"] = security.get_api_key_hash(plain_api_key)

        res = super().create(db, obj_in=api_key_obj)
        return UnsafeAPIKey(
            id=res.id,
            name=res.name,
            user_id=res.user_id,
            plain_api_key=plain_api_key,
            is_active=res.is_active,
        )


api_key_repository = APIKeyRepository(APIKey)