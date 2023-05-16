from backend.app.core.settings import settings
from backend.app.db.utils import DataInitializer
from backend.app.db.repositories.user_type import user_type as user_type_repository
from backend.app.db.repositories.user import user_repo
from backend.app.schemas.user import UserCreate
from sqlalchemy.orm import Session

from backend.tests.utils import (
    random_email,
    random_lasrra_id,
    random_phone,
    random_string,
)

FIRST_SUPERUSER_ADDRESS = settings.FIRST_SUPERUSER_ADDRESS
FIRST_SUPERUSER_FIRSTNAME = settings.FIRST_SUPERUSER_FIRSTNAME
FIRST_SUPERUSER_LASTNAME = settings.FIRST_SUPERUSER_LASTNAME
SUPERUSER_USER_TYPE = settings.SUPERUSER_USER_TYPE


def test_data_initializer_on_creating_user_types(db: Session):
    d = DataInitializer(db, skip_auto_initialization=True)

    random_test_type = random_string()

    d._create_user_type(random_test_type)

    user_type = user_type_repository.get_by_name(db, name=random_test_type)
    assert user_type.name == random_test_type


def test_data_initializer_on_creating_super_user(db: Session):
    d = DataInitializer(db)
    user_type = user_type_repository.get_by_name(db, name=SUPERUSER_USER_TYPE)

    user_in = UserCreate(
        first_name=FIRST_SUPERUSER_FIRSTNAME,
        last_name=FIRST_SUPERUSER_LASTNAME,
        address=FIRST_SUPERUSER_ADDRESS,
        phone=random_phone(),
        email=random_email(),
        password=random_string(10),
        lasrra_id=random_lasrra_id(),
        user_type_id=user_type.id,
    )

    d._create_superuser(user_in)

    user = user_repo.get_by_email(db, email=user_in.email)
    assert user