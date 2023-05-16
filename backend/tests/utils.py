from backend.app.api.routes.users import AGENT_EMPLOYEE_TYPE
import random
import string
from typing import Any, Dict

from backend.app.core.settings import settings
from backend.app.db.repositories.user import user_repo
from backend.app.db.repositories.user_type import user_type as user_type_repo
from backend.app.models.user import User
from backend.app.schemas.user import UserCreate
from sqlalchemy.orm import Session

from commonlib.validators import lasrra

AGENT = settings.AGENT
FIRST_SUPERUSER_EMAIL = settings.FIRST_SUPERUSER_EMAIL
REGULAR_USER_TYPE = settings.REGULAR_USER_TYPE
SUPERUSER_USER_TYPE = settings.SUPERUSER_USER_TYPE
Agent = settings.Agent
AgentEmployeeUser = settings.AgentEmployeeUser


def random_string(length: int = 32) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=length))


def random_email() -> str:
    return f"{random_string()}@{random_string()}.com"


def random_phone() -> str:
    return "".join(random.choices(string.digits, k=11))


def random_lasrra_id() -> str:
    prefix = random.choice(["LA", "LG"])
    workstation_id = "".join(random.choices(string.digits, k=3))
    number = "".join(random.choices(string.digits, k=6))
    dummy_check_sum = "X"
    if prefix == "LA":
        check_sum = lasrra._generate_lasrra_id_checksum_v1(
            prefix + workstation_id + number + dummy_check_sum
        )
    else:
        check_sum = lasrra._generate_lasrra_id_checksum_v2(
            prefix + workstation_id + number + dummy_check_sum
        )

    return prefix + workstation_id + number + str(check_sum)


def get_superuser_auth_header(db: Session) -> Dict[str, Any]:
    user = get_default_superuser(db)
    return generate_header_from_user_obj(user)


def get_default_superuser(db: Session) -> User:
    user = user_repo.get_by_email(db, email=FIRST_SUPERUSER_EMAIL)
    assert user, "user with email {} does not exists".format(FIRST_SUPERUSER_EMAIL)
    return user


def get_default_agent_user(db: Session) -> User:
    user = user_repo.get_by_email(db, email=Agent.EMAIL)
    assert user, "user with email {} does not exist".format(Agent.EMAIL)
    return user


def get_default_agent_employee_user(db: Session) -> User:
    AgentEmployeeUser
    user = user_repo.get_by_email(db, email=AgentEmployeeUser.EMAIL)
    assert user, "user with email {} does not exist".format(AgentEmployeeUser.EMAIL)
    return user


def get_agent_employee_user(db: Session) -> User:
    user = user_repo.get_by_email(db, email=AgentEmployeeUser.EMAIL)
    assert user, "user with email {} does not exist".format(AgentEmployeeUser.EMAIL)
    return user


def create_user_with_type(db: Session, type_: str):
    user_type = user_type_repo.get_by_name(db, name=type_)
    user_in = UserCreate(
        first_name=random_string(),
        last_name=random_string(),
        email=random_email(),
        password=random_string(),
        address=random_string(),
        phone=random_phone(),
        lasrra_id=random_lasrra_id(),
        user_type_id=user_type.id,
    )
    return user_repo.create(db, obj_in=user_in)


# def get_agent_user(db: Session):
#     return create_user_with_type(db=db, type_=AGENT)


def create_agent_user(db: Session) -> User:
    user = create_user_with_type(db=db, type_=AGENT)
    return activate_user(db, user)


def create_agent_employee_user(db: Session) -> User:
    user = create_user_with_type(db=db, type_=AGENT_EMPLOYEE_TYPE)
    return activate_user(db, user)


def create_superuser_user(db: Session) -> User:
    user = create_user_with_type(db=db, type_=SUPERUSER_USER_TYPE)
    return activate_user(db, user)


def generate_header_from_user_obj(user: User) -> Dict[str, Any]:
    return {"Authorization": "Token {}".format(user.generate_jwt())}


def activate_user(db: Session, user: User):
    return user_repo.activate(db, db_obj=user)


def generate_user_payload():
    first_name, last_name = random_string(), random_string()
    address = random_string()
    email = random_email()
    phone = random_phone()
    password = random_string()
    lasrra_id = random_lasrra_id()

    return {
        "first_name": first_name,
        "last_name": last_name,
        "address": address,
        "phone": phone,
        "email": email,
        "password": password,
        "lasrra_id": lasrra_id,
    }
