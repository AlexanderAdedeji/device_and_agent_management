from backend.app.core.settings import settings
from starlette.exceptions import HTTPException
from starlette.status import HTTP_403_FORBIDDEN
from backend.app.api.dependencies.db import get_db
from backend.app.api.errors import error_strings
from backend.app.api.errors.exceptions import (
    DisallowedLoginException,
    IncorrectLoginException,
)

from backend.app.db.repositories.user import user_repo
from backend.app.db.repositories.agent import agent_repo
from backend.app.schemas.user import UserInLogin, UserWithToken
from backend.app.schemas.user_type import UserTypeInDB
from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session


SUPERUSER_USER_TYPE = settings.SUPERUSER_USER_TYPE
AGENT_MANAGER = settings.AGENT_MANAGER
AGENT_SUPERVISOR= settings.AGENT_SUPERVISOR


router = APIRouter()


@router.post("/login", 
response_model=UserWithToken,
 name="Login",
 )
def login(
    db: Session = Depends(get_db),
    user_login: UserInLogin = Body(..., alias="user"),
    
) -> UserWithToken:
    """
    This route expects you to supply your credentials and if valid, returns a JWT for you to use to authenticate future requests.
    Only superusers,agent's managers and agent's supervisors are allowed to log in.
    """

    user = user_repo.get_by_email(db, email=user_login.email)
    
    if user:
        agent=  agent_repo.get(db, id=user.agent_id)
        if not agent:
            agent_name= None
            agent_id =None
        else:
            agent_name= agent.name
            agent_id =agent.id

    if user is None or not user.verify_password(user_login.password):
        raise IncorrectLoginException()

    if user.user_type.name not in [SUPERUSER_USER_TYPE, AGENT_MANAGER, AGENT_SUPERVISOR]:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail=error_strings.UNAUTHORIZED_ACTION
        )

    if not user.is_active:
        raise DisallowedLoginException(detail=error_strings.INACTIVE_USER_ERROR)
       

    token = user.generate_jwt()
    return UserWithToken(
        email=user.email,
        token=token,
        agent_name= agent_name,
        agent_id= agent_id,
        user_type=UserTypeInDB(id=user.user_type_id, name=user.user_type.name),
    )


    
