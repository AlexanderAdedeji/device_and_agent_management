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
    get_currently_authenticated_user,
    superuser_permission_dependency,
    manager_and_supervisor_and_superuser_permission_dependency
)
from backend.app.api.dependencies.db import get_db
from backend.app.api.errors.exceptions import (
    AlreadyExistsException,
    InvalidTokenException,
    ObjectNotFoundException,
    ServerException,
    UnauthorizedEndpointException,
)
from backend.app.core.settings import settings
from backend.app.db.repositories.device import device_repo
from backend.app.db.repositories.agent import agent_repo
from backend.app.db.repositories.reset_token import reset_token_repo
from backend.app.db.repositories.user import user_repo
from backend.app.db.repositories.user_type import user_type as user_type_repo
from backend.app.models import User
from backend.app.schemas.generic import GenericMessageResponse
from backend.app.schemas.user import (
    AgentProfile,

    AgentEmployeeUserCreateForm,
    ResetPasswordSchema,
    SlimUserInResponse,
    UserCreate,
    UserCreateForm,
    UserInResponse,
    UserUpdate,
)

from backend.app.schemas.agent import (
    Agent,
    AgentCreate,
    AgentCreateForm,
    AgentUpdate,
    AgentProfile,
    AgentInResponse
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



ACTIVATE_ACCOUNT_TEMPLATE_ID = settings.ACTIVATE_ACCOUNT_TEMPLATE_ID
CREATE_ACCOUNT_TEMPLATE_ID = settings.CREATE_ACCOUNT_TEMPLATE_ID
DEACTIVATE_ACCOUNT_TEMPLATE_ID = settings.DEACTIVATE_ACCOUNT_TEMPLATE_ID
RESET_PASSWORD_TEMPLATE_ID = settings.RESET_PASSWORD_TEMPLATE_ID
RESET_PASSWORD_URL = settings.RESET_PASSWORD_URL

router = APIRouter()




def check_unique_agent(db: Session, agent_in: AgentCreateForm):
    agent_with_same_email = agent_repo.get_by_email(db, email=agent_in.email)
    if agent_with_same_email:
        raise AlreadyExistsException(
            entity_name="agent with email {}".format(agent_in.email)
        )
    
    agent_with_same_name = agent_repo.get_by_name(db, name=agent_in.name)
    if agent_with_same_name:
        raise AlreadyExistsException()



@router.post(
    "/create_agent",
    response_model=AgentInResponse,
    dependencies=[Depends(superuser_permission_dependency)],
)
def create_agent(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_currently_authenticated_user),
    agent_in: AgentCreateForm,
    # background_tasks: BackgroundTasks,
) -> AgentInResponse:
    """
    Create a new agent user. You need to be a superuser to create an agent 
    The email and name must have never been used before on the platform.
    """
    check_unique_agent(db, agent_in)
    

    user_type = user_type_repo.get_by_name(db, name=AGENT)
    agent = agent_repo.create(
        db,
        obj_in=AgentCreate(
            **agent_in.dict(),
            user_type_id= user_type.id,
            created_by_id=current_user.id,
        ),
    )
    
    return AgentInResponse(
        id=agent.id,
        name=agent_in.name,
        email=agent_in.email,
        address=agent_in.address,
        user_type=UserTypeInDB(id=user_type.id, name=user_type.name),
        created_by_id=current_user.id,
    )




@router.get(
    "/all_agents",
    dependencies=[Depends(superuser_permission_dependency)],
    response_model=List[AgentInResponse]
    )

def get_all_agent(
    *,
    db:Session = Depends(get_db),
    current_user:User =Depends(get_currently_authenticated_user)
    )->List[AgentInResponse]:
    """
        This endpoint returns every agent in the database.
        Only a superuser can access this end point.
    """ 
    if (current_user.user_type.name != SUPERUSER_USER_TYPE ):
        raise HTTPException(HTTP_403_FORBIDDEN, detail="You need to be a SuperUser to access this route")
        
    allagents = agent_repo.get_all(db)
    

    return [
        AgentInResponse(
        id=agent.id,
        name=agent.name,
        email=agent.email,
        address=agent.address,
        user_type=UserTypeInDB(id=agent.user_type.id, name=agent.user_type.name),
        created_by_id=current_user.id,
    )
    for agent in allagents
            
     ]

        
    



# template_dict = UserCreationTemplateVariables(
#         name=f"{user.first_name} {user.last_name}",
#     ).dict()

#     background_tasks.add_task(
#         send_email_with_template,
#         client=core.PostmarkClient(server_token=settings.POSTMARK_API_TOKEN),
#         template_id=CREATE_ACCOUNT_TEMPLATE_ID,
#         # template_dict=template_dict,
#         recipient=agent.email,
#     )








@router.get(
    "/agent_profile/{agent_id}",
    response_model=AgentProfile,
    dependencies=[Depends(manager_and_supervisor_and_superuser_permission_dependency)],
)
def get_an_agent_profile(
    agent_id: int,
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_currently_authenticated_user),
) -> AgentProfile:
    """
    This endpoint gets all agent information, including the devices and users assigned to an agent.
    You need to be a superadmin to view all agents information
    You can view only your agent's own information if you are a manager or a supervisor.
    """
    
    agent = agent_repo.get(db, id=agent_id)
    
    if not agent:
        raise ObjectNotFoundException(detail=f"agent with id {agent_id} was not found")

    if (
        current_user.user_type.name != SUPERUSER_USER_TYPE
        and current_user.agent_id != agent_id
    ):
        raise HTTPException(
            HTTP_403_FORBIDDEN, detail="you can only view your own agent profile"
        )

    assigned_users = user_repo.get_all_users_with_agent_id(db, agent_id=agent_id)
    owned_devices = device_repo.get_all_devices_with_agent_id(db, agent_id=agent_id)

    employees = [
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
        for user in assigned_users
    ]
    devices = [
        DeviceInDB(
            id=device.id,
            name=device.name,
            mac_id=device.mac_id,      
            creator_id=device.creator_id,
            is_active=device.is_active,
            agent_id=device.agent_id,
            agent_name=agent.name,
            assigned_users=[
                SlimUserInResponse(
                    id=user.id,
                    email=user.email,
                    lasrra_id=user.lasrra_id,
                    user_type=UserTypeInDB(
                        id=user.user_type.id, name=user.user_type.name
                    ),
                )
                for user in device.assigned_users
            ],
        )
        for device in owned_devices
    ]

    return AgentProfile(
        agent=AgentInResponse(
            id=agent.id,
            name=agent.name,
            email=agent.email,
            address=agent.address,
            user_type=UserTypeInDB(
                id=agent.user_type_id,
                name=agent.user_type.name,
            ),
        ),
        devices=devices,
        employees=employees,
    )


