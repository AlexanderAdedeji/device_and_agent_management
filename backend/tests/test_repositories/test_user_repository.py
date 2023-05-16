from backend.app.schemas.user_type import UserTypeCreate
import pytest
from backend.app.core.settings import settings
from backend.app.db.repositories.user import user_repo
from backend.app.db.repositories.user_type import user_type as user_type_repo
from backend.app.schemas.user import UserCreate, UserUpdate
from backend.app.services.security import verify_password
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from backend.tests.utils import (
    create_agent_employee_user,
    create_agent_user,
    get_default_agent_user,
    random_email,
    random_phone,
    random_string,
    random_lasrra_id,
)
from backend.app.db.session import SessionLocal

AGENT_EMPLOYEE_TYPE = settings.AGENT_EMPLOYEE_TYPE
FIRST_SUPERUSER_EMAIL = settings.FIRST_SUPERUSER_EMAIL


USER_TYPE_ID = user_type_repo.create(
    SessionLocal(), obj_in=UserTypeCreate(name=random_string())
).id


def test_create_user(db: Session) -> None:
    email = random_email()
    user_in = UserCreate(
        first_name=random_string(),
        last_name=random_string(),
        email=email,
        password=random_string(),
        address=random_string(),
        phone=random_phone(),
        lasrra_id=random_lasrra_id(),
        user_type_id=USER_TYPE_ID,
    )
    user = user_repo.create(db, obj_in=user_in)

    assert user.email == email
    assert hasattr(user, "hashed_password")


def test_authenticate_user(db: Session) -> None:
    email = random_email()
    password = random_string()
    user_in = UserCreate(
        first_name=random_string(),
        last_name=random_string(),
        email=email,
        password=password,
        address=random_string(),
        phone=random_phone(),
        lasrra_id=random_lasrra_id(),
        user_type_id=USER_TYPE_ID,
    )
    user = user_repo.create(db, obj_in=user_in)
    authenticated_user = user_repo.authenticate(db, email=email, password=password)
    assert authenticated_user
    assert user.email == authenticated_user.email


def test_not_authenticate_invalid_user(db: Session) -> None:
    email = random_email()
    password = random_string()
    user = user_repo.authenticate(db, email=email, password=password)
    assert user is None


def test_check_if_created_user_is_active(db: Session) -> None:
    email = random_email()
    password = random_string()
    user_in = UserCreate(
        first_name=random_string(),
        last_name=random_string(),
        email=email,
        password=password,
        address=random_string(),
        phone=random_phone(),
        lasrra_id=random_lasrra_id(),
        user_type_id=USER_TYPE_ID,
    )
    user = user_repo.create(db, obj_in=user_in)
    assert user_repo.get(db, id=user.id).is_active is False


def test_check_if_automatically_added_user_is_superuser(db: Session) -> None:
    user = user_repo.get_by_email(db, email=FIRST_SUPERUSER_EMAIL)
    assert user.is_superuser is True


def test_check_if_newly_created_user_is_superuser(db: Session) -> None:
    email = random_email()
    password = random_string()
    user_in = UserCreate(
        first_name=random_string(),
        last_name=random_string(),
        email=email,
        password=password,
        address=random_string(),
        phone=random_phone(),
        lasrra_id=random_lasrra_id(),
        user_type_id=USER_TYPE_ID,
    )
    user = user_repo.create(db, obj_in=user_in)
    assert user_repo.get(db, id=user.id).is_superuser is False


def test_get_user(db: Session) -> None:
    user = user_repo.get_by_email(db, email=FIRST_SUPERUSER_EMAIL)
    user_2 = user_repo.get(db, id=user.id)
    assert user_2
    assert user_2 is user
    assert user.email == user_2.email
    assert jsonable_encoder(user) == jsonable_encoder(user_2)


def test_update_user(db: Session) -> None:
    user = create_agent_user(db)
    new_password = random_string()
    user_in_update = UserUpdate(password=new_password)
    user_repo.update(db, db_obj=user, obj_in=user_in_update)
    user_2 = user_repo.get(db, id=user.id)
    assert user_2
    assert user.email == user_2.email
    assert user.address == user_2.address
    assert verify_password(new_password, user_2.hashed_password)


def test_modify_superuser_status(db: Session) -> None:
    user = create_agent_employee_user(db)
    assert not user.is_superuser
    user_repo.set_as_superuser(db, user)
    assert user.is_superuser
    user_repo.set_usertype(
        db,
        db_obj=user,
        user_type=user_type_repo.get_by_name(db, name=AGENT_EMPLOYEE_TYPE),
    )
    assert not user.is_superuser
    assert user.user_type.name == AGENT_EMPLOYEE_TYPE


def test_modify_activation_status(db: Session) -> None:
    user = create_agent_employee_user(db)
    assert user.is_active

    user_repo.activate(db=db, db_obj=user)
    assert user.is_active

    user_repo.deactivate(db=db, db_obj=user)
    db.refresh(user)
    assert not user.is_active


def test_get_all_users_with_agent_id(db: Session) -> None:
    agent = get_default_agent_user(db)

    agent_employee = create_agent_employee_user(db)
    agent_employee.agent_id = agent.id
    user_repo.update(db, db_obj=agent_employee, obj_in={})

    db.refresh(agent_employee)

    assert agent_employee
    assert agent_employee.agent is agent

    assert agent_employee in user_repo.get_all_users_with_agent_id(
        db, agent_id=agent.id
    )

    agent_employee.agent_id = None
    user_repo.update(db, db_obj=agent_employee, obj_in={})

    db.refresh(agent_employee)

    assert agent_employee
    assert agent_employee.agent is None
