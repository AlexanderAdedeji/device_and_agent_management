from backend.app.core.settings import settings
from backend.app.models.user import User
from backend.app.db.errors import DBViolationError
from loguru import logger
from typing import Any, Dict, List


from backend.app.models.device import Device
from backend.app.db.repositories.base import Base
from backend.app.schemas.device import DeviceCreate, DeviceUser
from sqlalchemy.orm import Session
from backend.app.services import email
from backend.app.db.repositories.user import user_repo

DEACTIVATE_DEVICE_TEMPLATE_ID = settings.DEACTIVATE_DEVICE_TEMPLATE_ID
ACTIVATE_DEVICE_TEMPLATE_ID = settings.ACTIVATE_DEVICE_TEMPLATE_ID


class DeviceRepository(Base[Device]):
    def add_assigned_user(
        self, db: Session, *, device_obj: Device, user_obj: User
    ) -> Device:
        return self.add_assigned_users(db, device_obj=device_obj, user_objs=[user_obj])

    def add_assigned_users(
        self, db: Session, *, device_obj: Device, user_objs: List[User]
    ) -> Device:
        device_obj.assigned_users.extend(user_objs)
        db.add(device_obj)
        db.commit()
        db.refresh(device_obj)
        return device_obj

    def get_all_devices_with_creator_id(
        self, db: Session, *, creator_id: int
    ) -> List[Device]:
        return db.query(Device).filter(Device.creator_id == creator_id).all()

    def get_all_devices_with_agent_id(
        self, db: Session, *, agent_id: int
    ) -> List[Device]:
        return db.query(Device).filter(Device.agent_id == agent_id).all()

    def get_device_config(self, db: Session, *, device_obj: Device) -> Dict[str, Any]:
        users = []
        device_owner = user_repo.get(db, id=device_obj.agent_id)

        for user in [device_owner, *device_obj.assigned_users]:
            user: User
            users.append(DeviceUser(**user.to_json()))

        return {
            "users": users,
            "is_active": device_obj.is_active,
            "device_id": device_obj.id,
            "rabbitmq_uri": settings.EXTERNAL_RABBIT_MQ_URI,
            "secret_key": settings.SECRET_KEY,
            "api_base_uri": settings.API_BASE_URL,
        }

    def remove_assigned_user(
        self, db: Session, *, device_obj: Device, user_obj: User
    ) -> Device:
        return self.remove_assigned_users(
            db, device_obj=device_obj, user_objs=[user_obj]
        )

    def remove_assigned_users(
        self, db: Session, *, device_obj: Device, user_objs: List[User]
    ) -> Device:
        user_obj_set = set(user_objs)

        device_obj.assigned_users = [
            user for user in device_obj.assigned_users if user not in user_obj_set
        ]

        db.add(device_obj)
        db.commit()
        db.refresh(device_obj)
        return device_obj

    def activate_device(self, db: Session, *, device_obj: Device) -> Device:
        return super().update(db, db_obj=device_obj, obj_in={"is_active": True})

    def deactivate_device(self, db: Session, *, device_obj: Device) -> Device:
        return super().update(db, db_obj=device_obj, obj_in={"is_active": False})

    def mac_id_exists(self, db: Session, mac_id: str) -> bool:
        return bool(self.get_by_field(db, field_name="mac_id", field_value=mac_id))

    def create(self, db: Session, *, obj_in: DeviceCreate) -> Device:
        if self.mac_id_exists(db, mac_id=obj_in.mac_id):
            raise DBViolationError(
                "device with mac id {} already exists".format(obj_in.mac_id)
            )
            if self.name_exists(db, name=obj_in.name):
                raise DBViolationError(
                    "device with name {} already exists".format(obj_in.name)
                )
        return super().create(db, obj_in=obj_in)


device_repo = DeviceRepository(Device)
