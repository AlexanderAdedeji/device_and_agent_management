from typing import List

from fastapi.exceptions import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST

from backend.app.api.dependencies.authentication import (
    get_currently_authenticated_user,
    superuser_permission_dependency,
    manager_and_superuser_permission_dependency
)
from backend.app.api.dependencies.db import get_db
from backend.app.api.errors.exceptions import (
    AlreadyExistsException,
    ObjectNotFoundException,
)
from backend.app.core.settings import settings
from backend.app.models import User
from backend.app.models.agent import Agent
from backend.app.db.repositories.user_type import user_type as user_type_repo
from backend.app.db.repositories.agent import agent_repo
from backend.app.schemas.user_type import UserTypeCreate, UserTypeInDB
from backend.app.schemas.user import UserInResponse
from backend.app.schemas.agent import AgentInResponse
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.api.errors import error_strings


AGENT = settings.AGENT
SUPERUSER_USER_TYPE = settings.SUPERUSER_USER_TYPE
DEFAULT_USER_TYPES = settings.USER_TYPES

router = APIRouter()


@router.get(
    "/",
    response_model=List[UserTypeInDB],
    dependencies=[Depends(manager_and_superuser_permission_dependency)],
)
def retrieve_all_user_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_currently_authenticated_user),
) -> List[UserTypeInDB]:
    """
    This is used to retrieve the list of all user types in the application
    You need to be a superuser to use this endpoint.
    You send the token in as a header of the form \n
    <b>Authorization</b> : 'Token <b> {JWT} </b>'
    """

    user_types = user_type_repo.get_all(db)
    return [
        UserTypeInDB(id=user_type.id, name=user_type.name) for user_type in user_types
    ]


@router.post(
    "/",
    response_model=UserTypeInDB,
    dependencies=[Depends(superuser_permission_dependency)],
)
def create_user_type(
    *,
    db: Session = Depends(get_db),
    user_type_in: UserTypeCreate,
    current_user: User = Depends(get_currently_authenticated_user),
) -> UserTypeInDB:
    """
    This is used to create a new user type in the application
    You need to be a superuser to use this endpoint.
    You send the token in as a header of the form \n
    <b>Authorization</b> : 'Token <b> {JWT} </b>'
    """
    exists = bool(user_type_repo.get_by_name(db, name=user_type_in.name))
    if exists:
        raise AlreadyExistsException(
            detail=error_strings.ALREADY_EXISTS.format(
                "user type with name " + user_type_in.name
            )
        )

    user_type = user_type_repo.create(db, obj_in=user_type_in)
    return UserTypeInDB(id=user_type.id, name=user_type.name)


@router.put(
    "/{user_type_id}",
    response_model=UserTypeInDB,
    dependencies=[Depends(superuser_permission_dependency)],
)
def update_user_type(
    user_type_id: int,
    *,
    db: Session = Depends(get_db),
    user_type_in: UserTypeCreate,
    current_user: User = Depends(get_currently_authenticated_user),
) -> UserTypeInDB:
    """
    This is used to update an existing user type in the application
    You need to be a superuser to use this endpoint.
    You send the token in as a header of the form \n
    <b>Authorization</b> : 'Token <b> {JWT} </b>'
    """
    target_user_type = user_type_repo.get(db, id=user_type_id)
    if not target_user_type:
        raise ObjectNotFoundException()

    if target_user_type.name in DEFAULT_USER_TYPES:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"you can not update user type {target_user_type.name} as it is a default user type",
        )

    exists = bool(user_type_repo.get_by_name(db, name=user_type_in.name))

    if exists:
        raise AlreadyExistsException(
            detail=error_strings.ALREADY_EXISTS.format(
                "user type with name " + user_type_in.name
            )
        )

    updated_user_type = user_type_repo.update(
        db, db_obj=target_user_type, obj_in=user_type_in
    )
    return UserTypeInDB(id=updated_user_type.id, name=updated_user_type.name)


@router.delete(
    "/{user_type_id}",
    response_model=UserTypeInDB,
    dependencies=[Depends(superuser_permission_dependency)],
)
def delete_user_type(
    user_type_id: int,
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_currently_authenticated_user),
) -> List[UserTypeInDB]:
    """
    This is used to delete an existing user type in the application
    You need to be a superuser to use this endpoint.
    You send the token in as a header of the form \n
    <b>Authorization</b> : 'Token <b> {JWT} </b>'
    """
    target_user_type = user_type_repo.get(db, id=user_type_id)
    if not target_user_type:
        raise ObjectNotFoundException()

    if target_user_type.name in DEFAULT_USER_TYPES:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"you can not delete user type {target_user_type.name} as it is a default user type",
        )

    if len(target_user_type.users) > 0:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="you can not delete this user type because it has users associated to it",
        )

    deleted_user_type = user_type_repo.remove(db, id=target_user_type.id)
    return UserTypeInDB(id=deleted_user_type.id, name=deleted_user_type.name)


@router.get(
    "/{user_type_id}/all_users",
    # response_model=List[UserInResponse],
    dependencies=[Depends(superuser_permission_dependency)],
)
def get_all_users_of_user_type(
    user_type_id: int,
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_currently_authenticated_user),
) -> List[UserInResponse]:
    """
    This endpoint gets all the users and agent under a particular user type.
    Only superusers have access to this endpoint.
    """
    target_user_type = user_type_repo.get(db, id=user_type_id)
    


    if not target_user_type:
        raise ObjectNotFoundException()

    if target_user_type.name == AGENT:
        agents = agent_repo.get_all(db)
        return [
            AgentInResponse(
            id=agent.id,
            name=agent.name,
            email=agent.email,
            user_type=UserTypeInDB(id=agent.user_type.id, name=agent.user_type.name),
            address=agent.address,
            )
             for agent in agents
        ]


    return [
       
        
        UserInResponse(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            address=user.address,
            phone=user.phone,
            email=user.email,
            lasrra_id=user.lasrra_id,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            user_type=UserTypeInDB(id=user.user_type.id, name=user.user_type.name),
            created_by_id=user.created_by_id,
            agent_id=user.agent_id,
            agent_name=agent_repo.get_name(db, id=user.agent_id)
        )
        
        for user in target_user_type.users
    ]


# @router.get(
#     "/{user_type_id}/all_users",
#     response_model=List[UserInResponse],
#     dependencies=[Depends(superuser_permission_dependency)],
# )
# def get_all_agent_of_user_type(
#     user_type_id: int,
#     *,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_currently_authenticated_user),
# ) -> List[UserInResponse]:
#     """
#     This endpoint gets all the users under a particular user type.
#     Only superusers have access to this endpoint.
#     """
#     target_user_type = user_type_repo.get(db, id=user_type_id)
#     if not target_user_type:
#         raise ObjectNotFoundException()

#     return [
#         UserInResponse(
#             id=user.id,
#             first_name=user.first_name,
#             last_name=user.last_name,
#             address=user.address,
#             phone=user.phone,
#             email=user.email,
#             lasrra_id=user.lasrra_id,
#             is_active=user.is_active,
#             is_superuser=user.is_superuser,
#             user_type=UserTypeInDB(id=user.user_type.id, name=user.user_type.name),
#             created_by_id=user.created_by_id,
#             agent_id=user.agent_id,
#         )
#         for user in target_user_type.users
#     ]
