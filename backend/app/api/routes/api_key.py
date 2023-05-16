from typing import List

from backend.app.api.dependencies.authentication import (
    get_currently_authenticated_user,
    superuser_permission_dependency,
    manager_and_superuser_permission_dependency
)
from backend.app.api.dependencies.db import get_db
from backend.app.api.errors.exceptions import (
    ObjectNotFoundException,
    UnauthorizedEndpointException,
)
from backend.app.db.repositories.api_key import api_key_repository
from backend.app.models import User
from backend.app.schemas.api_key import (
    APIKey,
    APIKeyCreate,
    APIKeyInResponse,
    UnsafeAPIKey,
)
from fastapi import APIRouter
from fastapi.param_functions import Depends
from sqlalchemy.orm import Session

router = APIRouter()


@router.get(
    "/all",
    response_model=List[APIKeyInResponse],
    dependencies=[Depends(superuser_permission_dependency)],
)
def get_all_api_keys_in_system(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_currently_authenticated_user),
):
    """
    This endpoint gets all the API keys in the sytem
    You need to be a superuser to use this endpoint
    """
    api_keys = api_key_repository.get_all(db)
    return [
        APIKeyInResponse(id=api_key.id, name=api_key.name, is_active=api_key.is_active)
        for api_key in api_keys
    ]


@router.get(
    "/",
    response_model=List[APIKeyInResponse],
    dependencies=[Depends(manager_and_superuser_permission_dependency)],
)
def get_all_current_users_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_currently_authenticated_user),
):
    """
    This endpoint gets all the API keys belonging to the current user (i.e the user with the Token).
    You need to be a superuser or an agent's Manager to use this endpoint
    """


    api_keys = api_key_repository.get_all_with_user_id(db, user_id=current_user.id)

        

    return [
        APIKeyInResponse(id=api_key.id, name=api_key.name, is_active=api_key.is_active)
        for api_key in api_keys
    ]






@router.post(
    "/",
    response_model=UnsafeAPIKey,
    dependencies=[Depends(manager_and_superuser_permission_dependency)],
)
def create_api_key(
    api_key: APIKey,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_currently_authenticated_user),
):
    """
    This endpoint allows a superuser or an agent's manager to create an API key.
    Note that the response gotten here contains the plain text api key and must be stored safely as it can not be shown to the user again.
    """
    return api_key_repository.create(
        db, api_key_obj=APIKeyCreate(**api_key.dict(), user_id=current_user.id)
    )


@router.delete(
    "/{api_key_id}",
    response_model=APIKeyInResponse,
    dependencies=[Depends(manager_and_superuser_permission_dependency)],
)
def deactivate_api_key(
    api_key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_currently_authenticated_user),
):
    """
    This endpoint allows a superuser or an agent's manager to deactive an API key that they currently own.
    You need to be the owner of the API key that you want to deactivate.
    """
    api_key = api_key_repository.get(db, id=api_key_id)
    if not api_key:
        raise ObjectNotFoundException()

    if not api_key.user is current_user:
        raise UnauthorizedEndpointException()

    api_key = api_key_repository.mark_as_inactive(db, api_key_obj=api_key)
    return APIKeyInResponse(
        id=api_key.id, name=api_key.name, is_active=api_key.is_active
    )
