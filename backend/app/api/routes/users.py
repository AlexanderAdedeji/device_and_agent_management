from datetime import datetime
from typing import List
from app.schemas.device import DeviceInDB

from backend.app.schemas.email import (
    ResetPasswordEmailTemplateVariables,
    UserActivationTemplateVariables,
    UserCreationTemplateVariables,
    UserDeactivationTemplateVariables,
)
from backend.app.tasks import devices
from backend.app.api.dependencies.authentication import (
    manager_and_superuser_permission_dependency,
    manager_and_supervisor_and_superuser_permission_dependency,
    get_currently_authenticated_user,
    superuser_permission_dependency,
)
from backend.app.api.dependencies.db import get_db
from backend.app.api.errors.exceptions import (
    AlreadyExistsException,
    InvalidTokenException,
    ObjectNotFoundException,
    ServerException,

    AgentEmployeeUserNotSelectedException,
    UnauthorizedEndpointException,
)
from backend.app.core.settings import settings
from backend.app.db.repositories.device import device_repo
from backend.app.db.repositories.reset_token import reset_token_repo
from backend.app.db.repositories.user import user_repo
from backend.app.db.repositories.agent import agent_repo
from backend.app.db.repositories.user_type import user_type as user_type_repo
from backend.app.models import User
from backend.app.schemas.generic import GenericMessageResponse
from backend.app.schemas.user import (
    AgentProfile,
    MangerCreateForm,
    AgentEmployeeUserCreateForm,
    ResetPasswordSchema,
    SlimUserInResponse,
    UserCreate,
    UserCreateForm,
    UserInResponse,
    UserUpdate,
)
from backend.app.schemas.user_type import UserTypeInDB
from backend.app.services.email import send_email_with_template
from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.exceptions import HTTPException
from itsdangerous.exc import BadSignature
from postmarker import core
from pydantic.networks import EmailStr
from sqlalchemy.orm import Session
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN

# AGENT_EMPLOYEE_TYPE = settings.AGENT_EMPLOYEE_TYPE
AGENT = settings.AGENT
REGULAR_USER_TYPE = settings.REGULAR_USER_TYPE
SUPERUSER_USER_TYPE = settings.SUPERUSER_USER_TYPE
AGENT_MANAGER = settings.AGENT_MANAGER
AGENT_OFFICER = settings.AGENT_OFFICER
AGENT_SUPERVISOR =settings.AGENT_SUPERVISOR



ACTIVATE_ACCOUNT_TEMPLATE_ID = settings.ACTIVATE_ACCOUNT_TEMPLATE_ID
CREATE_ACCOUNT_TEMPLATE_ID = settings.CREATE_ACCOUNT_TEMPLATE_ID
DEACTIVATE_ACCOUNT_TEMPLATE_ID = settings.DEACTIVATE_ACCOUNT_TEMPLATE_ID
RESET_PASSWORD_TEMPLATE_ID = settings.RESET_PASSWORD_TEMPLATE_ID
RESET_PASSWORD_URL = settings.RESET_PASSWORD_URL

router = APIRouter()


def check_unique_user(db: Session, user_in: UserCreate):
    user_with_same_email = user_repo.get_by_email(db, email=user_in.email)
    if user_with_same_email:
        raise AlreadyExistsException(
            entity_name="user with email {}".format(user_in.email)
        )

    user_with_same_lasrra_id = user_repo.get_by_field(
        db, field_name="lasrra_id", field_value=user_in.lasrra_id
    )
    if user_with_same_lasrra_id:
        raise AlreadyExistsException(
            entity_name="user with lasrra_id {}".format(user_in.lasrra_id)
        )

    user_with_same_phone = user_repo.get_by_field(
        db, field_name="phone", field_value=user_in.phone
    )
    if user_with_same_phone:
        raise AlreadyExistsException(
            entity_name="user with phone {}".format(user_in.phone)
        )


@router.get("/me")
def retrieve_current_user(
    current_user: User = Depends(get_currently_authenticated_user),
) -> UserInResponse:
    """
    This is used to retrieve the currently logged-in user's profile.
    You need to send a token in and it returns a full profile of the currently logged in user.
    You send the token in as a header of the form \n
    <b>Authorization</b> : 'Token <b> {JWT} </b>'
    """
    return UserInResponse(
        id=current_user.id,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        address=current_user.address,
        phone=current_user.phone,
        email=current_user.email,
        lasrra_id=current_user.lasrra_id,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        agent_id=current_user.agent_id,
        user_type=UserTypeInDB(
            id=current_user.user_type.id,
            name=current_user.user_type.name,
        ),
    )




@router.post(
    "/create_agent_employee_user",
    response_model=UserInResponse,
    dependencies=[Depends(manager_and_superuser_permission_dependency)],
)
def create_agent_employee_user(
    *,
    db: Session = Depends(get_db),
    user_in: AgentEmployeeUserCreateForm,
    current_user: User = Depends(get_currently_authenticated_user),
    background_tasks: BackgroundTasks,
) -> UserInResponse:
    """
    Create a new agent employee user.
    You need to be a manager or a superuser to create a user
    The email,lasrra ID & phone number must have never been used before on the platform.
    """
    check_unique_user(db, user_in)
    user_type = user_type_repo.get_by_id(db, id=user_in.user_type_id)
    if user_type.name in [AGENT_SUPERVISOR, AGENT_OFFICER]:
        user_type_name =user_type_repo.get_by_name(db, name=user_type.name)
    else:
        raise AgentEmployeeUserNotSelectedException()

    if not user_type:
        raise ServerException()
    user = user_repo.create(
        db,
        obj_in=UserCreate(
            **user_in.dict(),
            created_by_id=current_user.id,
        ),
    )

    template_dict = UserCreationTemplateVariables(
        name=f"{user.first_name} {user.last_name}",
    ).dict()

    background_tasks.add_task(
        send_email_with_template,
        client=core.PostmarkClient(server_token=settings.POSTMARK_API_TOKEN),
        template_id=CREATE_ACCOUNT_TEMPLATE_ID,
        template_dict=template_dict,
        recipient=user.email,
    )

    return UserInResponse(
        id=user.id,
        email=user_in.email,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        address=user_in.address,
        phone=user_in.phone,
        lasrra_id=user_in.lasrra_id,
        is_active=user.is_active,
        agent_id=user.agent_id,
        is_superuser=user.is_superuser,
        user_type=UserTypeInDB(id=user_type.id, name=user_type.name),
        created_by_id=current_user.id,
    )




@router.post(
    "/create_agent_manager_user",
    response_model=UserInResponse,
    dependencies=[Depends(superuser_permission_dependency)],
)
def create_agent_manager_user(
    *,
    db: Session = Depends(get_db),
    user_in: MangerCreateForm,
    current_user: User = Depends(get_currently_authenticated_user),
    background_tasks: BackgroundTasks,
) -> UserInResponse:
    """
    Create a new agent manager user.
    You need to be a superuser to create an agent manager
    The email,lasrra ID & phone number must have never been used before on the platform.
    """
    check_unique_user(db, user_in)
    user_type = user_type_repo.get_by_name(db, name=AGENT_MANAGER)
    if not user_type:
        raise ServerException()
    user = user_repo.create(
        db,
        obj_in=UserCreate(
            **user_in.dict(),
            user_type_id=user_type.id,
            created_by_id=current_user.id,
        ),
    )

    template_dict = UserCreationTemplateVariables(
        name=f"{user.first_name} {user.last_name}",
    ).dict()

    background_tasks.add_task(
        send_email_with_template,
        client=core.PostmarkClient(server_token=settings.POSTMARK_API_TOKEN),
        template_id=CREATE_ACCOUNT_TEMPLATE_ID,
        template_dict=template_dict,
        recipient=user.email,
    )

    return UserInResponse(
        id=user.id,
        email=user_in.email,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        address=user_in.address,
        phone=user_in.phone,
        lasrra_id=user_in.lasrra_id,
        is_active=user.is_active,
        agent_id=user.agent_id,
        is_superuser=user.is_superuser,
        user_type=UserTypeInDB(id=user_type.id, name=user_type.name),
        created_by_id=current_user.id,
    )






@router.put("/", response_model=UserInResponse)
def update_user(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_currently_authenticated_user),
    user_in: UserUpdate,
    background_tasks: BackgroundTasks,
) -> UserInResponse:
    """
    This endpoint is used to make changes to the user's profile
    """
    user_with_same_email = user_repo.get_by_email(db, email=user_in.email)
    if user_with_same_email:
        raise AlreadyExistsException(
            entity_name="user with email {}".format(user_in.email)
        )

    user_with_same_phone = user_repo.get_by_field(
        db, field_name="phone", field_value=user_in.phone
    )
    if user_with_same_phone:
        raise AlreadyExistsException(
            entity_name="user with phone {}".format(user_in.phone)
        )

    user = user_repo.update(db, db_obj=current_user, obj_in=user_in)

    concerned_devices = user.devices
    for device in concerned_devices:
        background_tasks.add_task(
            devices.send_notification_to_devices, device.mac_id, " "
        )

    return UserInResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        address=user.address,
        phone=user.phone,
        lasrra_id=user.lasrra_id,
        is_active=user.is_active,
        agent_id=user.agent_id,
        is_superuser=user.is_superuser,
        user_type=UserTypeInDB(id=user.user_type.id, name=user.user_type.name),
    )


@router.get(
    "/activate/{user_id}",
    response_model=UserInResponse,
    dependencies=[Depends(manager_and_supervisor_and_superuser_permission_dependency)],
)
def activate_user(
    user_id: int,
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_currently_authenticated_user),
    background_tasks: BackgroundTasks,
) -> UserInResponse:
    """
    This endpoint activates a user.
    You need a superuser or the manager of the agent who owns this user (i.e the user's agent_id is your agent id) to do this.
    """
    user = user_repo.get(db, id=user_id)
    if not user:
        raise ObjectNotFoundException()
    if (
        current_user.user_type.name not in [SUPERUSER_USER_TYPE, AGENT_MANAGER, AGENT_SUPERVISOR]
        and user.agent_id != current_user.id
    ):
        raise UnauthorizedEndpointException()

    user = user_repo.activate(db, db_obj=user)
    template_dict = UserActivationTemplateVariables(
        name=f"{user.first_name} {user.last_name}",
    ).dict()

    background_tasks.add_task(
        send_email_with_template,
        client=core.PostmarkClient(server_token=settings.POSTMARK_API_TOKEN),
        template_id=ACTIVATE_ACCOUNT_TEMPLATE_ID,
        template_dict=template_dict,
        recipient=user.email,
    )

    concerned_devices = user.devices
    for device in concerned_devices:
        background_tasks.add_task(
            devices.send_notification_to_devices, device.mac_id, " "
        )

    return UserInResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        address=user.address,
        phone=user.phone,
        lasrra_id=user.lasrra_id,
        is_active=user.is_active,
        agent_id=user.agent_id,
        is_superuser=user.is_superuser,
        user_type=UserTypeInDB(id=user.user_type.id, name=user.user_type.name),
    )


@router.get(
    "/deactivate/{user_id}",
    response_model=UserInResponse,
    dependencies=[Depends(manager_and_supervisor_and_superuser_permission_dependency)],
)
def deactivate_user(
    user_id: int,
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_currently_authenticated_user),
    background_tasks: BackgroundTasks,
) -> UserInResponse:
    """
    This endpoint de-activates a user.
    You need a superuser or the manager of the agent who owns this user (i.e the user's agent_id is your agent id) to do this.
    """
    user = user_repo.get(db, id=user_id)
    if not user:
        raise ObjectNotFoundException()

    if (
        current_user.user_type.name  not in [SUPERUSER_USER_TYPE, AGENT_MANAGER, AGENT_SUPERVISOR]
        and user.agent_id != current_user.id
    ):
        raise UnauthorizedEndpointException()

    user = user_repo.deactivate(db, db_obj=user)
    template_dict = UserDeactivationTemplateVariables(
        name=f"{user.first_name} {user.last_name}",
    ).dict()

    background_tasks.add_task(
        send_email_with_template,
        client=core.PostmarkClient(server_token=settings.POSTMARK_API_TOKEN),
        template_id=DEACTIVATE_ACCOUNT_TEMPLATE_ID,
        template_dict=template_dict,
        recipient=user.email,
    )

    concerned_devices = user.devices
    for device in concerned_devices:
        background_tasks.add_task(
            devices.send_notification_to_devices, device.mac_id, " "
        )

    return UserInResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        address=user.address,
        phone=user.phone,
        lasrra_id=user.lasrra_id,
        is_active=user.is_active,
        agent_id=user.agent_id,
        is_superuser=user.is_superuser,
        user_type=UserTypeInDB(id=user.user_type.id, name=user.user_type.name),
    )


@router.get(
    "/grant_superuser_status/{user_id}",
    dependencies=[Depends(superuser_permission_dependency)],
)
def grant_superuser_status(
    user_id: int,
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_currently_authenticated_user),
) -> User:
    """
    This endpoint makes a given user a superuser.
    You need to be a superuser to use this endpoint.
    """
    user = user_repo.get(db, id=user_id)
    if not user:
        raise ObjectNotFoundException()

    user = user_repo.set_as_superuser(db, db_obj=user)
    return UserInResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        address=user.address,
        phone=user.phone,
        lasrra_id=user.lasrra_id,
        is_active=user.is_active,
        agent_id=user.agent_id,
        is_superuser=user.is_superuser,
        user_type=UserTypeInDB(id=user.user_type.id, name=user.user_type.name),
    )


@router.get(
    "/remove_superuser_status/{user_id}",
    dependencies=[Depends(superuser_permission_dependency)],
)
def remove_superuser_status(
    user_id: int,
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_currently_authenticated_user),
) -> User:
    """
    This endpoint removes a given user from being superuser.
    You need to be a superuser to use this endpoint.
    The user becomes a REGULAR user upon performing this operation
    """
    user = user_repo.get(db, id=user_id)
    if not user:
        raise ObjectNotFoundException()

    regular_user_type_obj = user_type_repo.get_by_name(db, name=REGULAR_USER_TYPE)
    superuser_user_type_obj = user_type_repo.get_by_name(db, name=SUPERUSER_USER_TYPE)

    if not regular_user_type_obj or not superuser_user_type_obj:
        raise ServerException()

    if user.user_type_id != superuser_user_type_obj.id:
        raise HTTPException(HTTP_400_BAD_REQUEST, "user is not a superuser")

    user = user_repo.set_usertype(db, db_obj=user, user_type=regular_user_type_obj)

    return UserInResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        address=user.address,
        phone=user.phone,
        lasrra_id=user.lasrra_id,
        is_active=user.is_active,
        agent_id=user.agent_id,
        is_superuser=user.is_superuser,
        user_type=UserTypeInDB(id=user.user_type.id, name=user.user_type.name),
    )


@router.post(
    "/{user_id}/change_agent/{agent_id}",
    dependencies=[Depends(superuser_permission_dependency)],
    response_model=UserInResponse,
)


def change_agent(
    *,
    user_id: int,
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_currently_authenticated_user),
    background_tasks: BackgroundTasks,
) -> UserInResponse:
    """
    This endpoint changes the agent of the user with user_id, to the agent with id of agent_id, .
    You need to be a superuser to use this endpoint.
    When you change the agent of a user, he loses all the devices he was previosuly assigned to
    """
    user = user_repo.get(db, id=agent_id)
    user_to_be_reassigned = user_repo.get(db, id=user_id)

    if not user:
        raise ObjectNotFoundException(detail=f"user with id {agent_id} not found")
    if not user_to_be_reassigned:
        raise ObjectNotFoundException(detail=f"user with id {user_id} not found")

    if user is user_to_be_reassigned:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="can not assign to self"
        )

    user_is_not_agent_user = user.user_type.name != AGENT
    user_to_be_reassigned_is_not_agent_employee = (
        user_to_be_reassigned.user_type.name != AGENT_EMPLOYEE_TYPE
    )

    if user_is_not_agent_user or user_to_be_reassigned_is_not_agent_employee:
        detail = "user with id {} is not {}"
        if user_is_not_agent_user:
            detail = detail.format(user.id, "agent user")
        else:
            detail = detail.format(user_to_be_reassigned.id, "agent employee")
        raise UnauthorizedEndpointException(detail=detail)

    user_to_be_reassigned.agent_id = user.id
    user_to_be_reassigned = user_repo.update(
        db, db_obj=user_to_be_reassigned, obj_in={}
    )

    concerned_devices = user_to_be_reassigned.devices

    for device in concerned_devices:
        background_tasks.add_task(
            device_repo.remove_assigned_user,
            db=db,
            device_obj=device,
            user_obj=user_to_be_reassigned,
        )

    return UserInResponse(
        id=user_to_be_reassigned.id,
        first_name=user_to_be_reassigned.first_name,
        last_name=user_to_be_reassigned.last_name,
        address=user_to_be_reassigned.address,
        phone=user_to_be_reassigned.phone,
        email=user_to_be_reassigned.email,
        lasrra_id=user_to_be_reassigned.lasrra_id,
        is_active=user_to_be_reassigned.is_active,
        agent_id=user_to_be_reassigned.agent_id,
        is_superuser=user_to_be_reassigned.is_superuser,
        user_type=UserTypeInDB(
            id=user_to_be_reassigned.user_type.id,
            name=user_to_be_reassigned.user_type.name,
        ),
    )


@router.get(
    "/get_all_current_user_employees",
    dependencies=[Depends(manager_and_superuser_permission_dependency)],
    response_model=List[UserInResponse],
)
def get_all_current_user_employees(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_currently_authenticated_user),
) -> List[UserInResponse]:
    """
    This endpoint gets all the agent employees under the currently authenticated user, .
    You have to be an agent's Manager or superuser to use this endpoint.
    """

  
    agent_employees = user_repo.get_all_users_with_agent_id(
        db, agent_id=current_user.agent_id
    )

    return [
        UserInResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            address=user.address,
            phone=user.phone,
            lasrra_id=user.lasrra_id,
            is_active=user.is_active,
            agent_id=user.agent_id,
            is_superuser=user.is_superuser,
            user_type=UserTypeInDB(id=user.user_type.id, name=user.user_type.name),
            created_by_id=current_user.id,
        )
        for user in agent_employees
    ]


@router.get("/reset_password/{email}")
def reset_user_password(
    email: EmailStr,
    *,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks,
) -> GenericMessageResponse:
    """
    This endpoint requests a reset of the password for the given email.
    An email containing a link to the reset the password is sent to the user with the supplied email, if the user exists.
    """
    user = user_repo.get_by_email(db, email=email)
    if not user:
        raise ObjectNotFoundException()

    reset_token = user.generate_password_reset_token(db)
    # reset_link = RESET_PASSWORD_URL + reset_token.token
    reset_link = RESET_PASSWORD_URL+'?k=' + reset_token.token
    template_dict = ResetPasswordEmailTemplateVariables(
        name=f"{user.first_name} {user.last_name}", reset_link=reset_link
    ).dict()

    background_tasks.add_task(
        send_email_with_template,
        client=core.PostmarkClient(server_token=settings.POSTMARK_API_TOKEN),
        template_id=RESET_PASSWORD_TEMPLATE_ID,
        template_dict=template_dict,
        recipient=user.email,
    )

    return GenericMessageResponse(message="password reset link sent to " + email)


@router.post("/reset_password/")
def reset_user_password(
    *,
    db: Session = Depends(get_db),
    reset_info: ResetPasswordSchema,
    background_tasks: BackgroundTasks,
) -> GenericMessageResponse:
    try:
        token = reset_token_repo.get_by_field(
            db, field_name="token", field_value=reset_info.token
        )

        if not token or token.used:
            detail = "token is used" if token and token.used else "invalid token"
            raise InvalidTokenException(detail=detail)

        if token.expires_at <= datetime.now():
            raise ValueError("expired token")

        user = token.user
        user_repo.update(db, db_obj=user, obj_in={"password": reset_info.password})

        reset_token_repo.mark_as_used(db, token_obj=token)
        concerned_devices = user.devices
        for device in concerned_devices:
            background_tasks.add_task(
                devices.send_notification_to_devices, device.mac_id, " "
            )

        return GenericMessageResponse(
            message="password of user with email {} reset succesfully".format(
                user.email
            )
        )

    except ValueError as e:
        return e
        # raise InvalidTokenException(detail=str(e))
        # print(str(e))
    except BadSignature:
        raise InvalidTokenException()

@router.get('/userProfile/{user_id}', response_model=UserInResponse,dependencies=[Depends(manager_and_supervisor_and_superuser_permission_dependency)])
def get_user_profile(*,
    
    user_id:int,
    db:Session = Depends(get_db),
    current_user:User =Depends(get_currently_authenticated_user),
)->UserInResponse:

    """This endpoint gets all relevant information about a user that
     is in the system, You need to be a Superuser, a manager of the
      user or a supervisor of the user in order to be able to view this
       information"""
    user = user_repo.get(db, id=user_id)
    if not user:
        raise ObjectNotFoundException(detail=f"User with id {user_id} was not found")

    if(current_user.user_type.name !=SUPERUSER_USER_TYPE and current_user.agent_id != user.agent_id ):
        raise HTTPException(
            HTTP_403_FORBIDDEN, detail="You can only view a User in you agency"
        )

    agent = agent_repo.get(db, id= user.agent_id)


    
    # if not agent:
    #     agent = {'name':'SuperUser'}

    return UserInResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            address=user.address,
            phone=user.phone,
            lasrra_id=user.lasrra_id,
            is_active=user.is_active,
            agent_id=user.agent_id,
            is_superuser=user.is_superuser,
            user_type=UserTypeInDB(id=user.user_type.id, name=user.user_type.name),
            created_by_id=current_user.id,
            agent_name = agent.name if agent else 'Super-User'
    )







@router.get("/all/", dependencies=[Depends(superuser_permission_dependency)])
def get_all_users_in_system(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_currently_authenticated_user),
) -> GenericMessageResponse:
    """
    This endpoint gets all the users in the system, you need to be a superuser to access this endpoint
    """
    all_users = user_repo.get_all(db)

    return [
        UserInResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            address=user.address,
            phone=user.phone,
            lasrra_id=user.lasrra_id,
            is_active=user.is_active,  
            is_superuser=user.is_superuser,
            user_type=UserTypeInDB(id=user.user_type.id, name=user.user_type.name),
            created_by_id=user.created_by_id,
            agent_id=user.agent_id,
            agent_name=agent_repo.get_name(db, id=user.agent_id)
        )
        for user in all_users
    ]