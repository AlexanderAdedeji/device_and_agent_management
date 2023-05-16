from typing import List
from backend.app.schemas.email import (
    DeviceActivationTemplateVariables,
    DeviceDeactivationTemplateVariables,
)
from backend.app.services.email import send_email_with_template
from backend.app.tasks.devices import send_notification_to_devices
from postmarker import core

from starlette.background import BackgroundTasks

from backend.app.api.dependencies.authentication import (
    DeviceAPIKeyHeader,
    superuser_permission_dependency,
    manager_and_supervisor_and_superuser_permission_dependency,
    manager_and_superuser_permission_dependency,
    get_currently_authenticated_user,
)
from backend.app.api.dependencies.db import get_db
from backend.app.api.errors.error_strings import (
    ALREADY_EXISTS,
    INVALID_API_KEY,
    NOT_AN_AGENT_EMPLOYEE_ERROR,
    NOT_AN_AGENT_OFFICER_ERROR,
    NOT_AN_AGENT_ERROR,
    NOT_FOUND,
)
from backend.app.api.errors.exceptions import (
    AlreadyExistsException,
    InactiveDeviceException,
    ObjectNotFoundException,
    UnauthorizedEndpointException,
)
from backend.app.core.settings import settings
from backend.app.db.repositories.api_key import api_key_repository
from backend.app.db.repositories.device import device_repo
from backend.app.db.repositories.user import user_repo
from backend.app.db.repositories.agent import agent_repo
from backend.app.models.device import Device
from backend.app.models.user import User
from backend.app.schemas.device import (
    DeviceConfig,
    DeviceCreate,
    DeviceInBody,
    DeviceInDB,
    DeviceMetaData,
    DeviceUpdate,
    DeviceUser,
    DeviceUserUpdate,
)
from backend.app.schemas.user import SlimUserInResponse
from backend.app.schemas.user_type import UserTypeInDB
from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from fastapi.param_functions import Security
from sqlalchemy.orm import Session
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN

AGENT = settings.AGENT
SUPERUSER_USER_TYPE = settings.SUPERUSER_USER_TYPE
# AGENT_EMPLOYEE_USER_TYPE = settings.AGENT_EMPLOYEE_TYPE
AGENT_OFFICER =settings.AGENT_OFFICER
API_KEY_AUTH_ENABLED = settings.API_KEY_AUTH_ENABLED

DEACTIVATE_DEVICE_TEMPLATE_ID = settings.DEACTIVATE_DEVICE_TEMPLATE_ID
ACTIVATE_DEVICE_TEMPLATE_ID = settings.ACTIVATE_DEVICE_TEMPLATE_ID


def can_access_device_obj(device: Device, user: User):
    """
    The user can access this device on 3 conditions
    1. the user is a superuser
    2. the user created this device
    3. the user is currently assigned to the agent of the device
    """
    return (
        user.user_type.name == 'SUPERUSER'
        or device.creator_id == user.id
        or device.agent_id == user.agent_id
    )


router = APIRouter()


@router.post(
    "/",
    response_model=DeviceInDB,
    dependencies=[Depends(manager_and_superuser_permission_dependency)],
)
def create_device(
    device_in: DeviceInBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_currently_authenticated_user),
) -> DeviceInDB:
    """
    This endpoint is used to create a device.
    You need to be an agent's manager, or superuser to create a device.
    """
    mac_id_exists = device_repo.get_by_field(
        db, field_name="mac_id", field_value=device_in.mac_id
    )
    if mac_id_exists:
        raise AlreadyExistsException(
            detail=ALREADY_EXISTS.format(f"device with mac id {device_in.mac_id}")
        )

    name_exists = device_repo.get_by_field(
        db, field_name="name", field_value=device_in.name
    )

    if name_exists:
        raise AlreadyExistsException(
            detail=ALREADY_EXISTS.format(f"device with name {device_in.name}")
        )



    agent = agent_repo.get(db, id=device_in.agent_id)
    
    if not agent:
        raise HTTPException(
            HTTP_400_BAD_REQUEST,
            detail=f"agent with id {device_in.agent_id} does not exist",
        )

    # if agent.user_type.name != AGENT:
    #     raise UnauthorizedEndpointException(detail=f"the user with id {agent.id} is not an agent")


    device = device_repo.create(
        db, obj_in=DeviceCreate(mac_id=device_in.mac_id, name=device_in.name, creator_id=current_user.id,agent_id=agent.id)
    )

    return DeviceInDB(
        id=device.id,
        name=device.name,
        mac_id=device.mac_id,
        creator_id=device.creator_id,
        is_active=device.is_active,
        agent_id=device.agent_id,
        assigned_users=[
            SlimUserInResponse(
                id=user.id,
                email=user.email,
                lasrra_id=user.lasrra_id,
                user_type=UserTypeInDB(id=user.user_type.id, name=user.user_type.name),
            )
            for user in device.assigned_users
        ],
    )


@router.get(
    "/",
    response_model=List[DeviceInDB],
    dependencies=[Depends(superuser_permission_dependency)],
)
def get_all_existing_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_currently_authenticated_user),
) -> List[DeviceInDB]:
    """
    This endpoint gives you all the devices which exist.
    You need to be a superuser to use this endpoint.

    """
    devices = device_repo.get_all(db)
    return [
        DeviceInDB(
            id=device.id,
            name=device.name,
            mac_id=device.mac_id,
            creator_id=device.creator_id,
            is_active=device.is_active,
            agent_id=device.agent_id,
            agent_name=agent_repo.get_name(db, id=device.agent_id),
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
        for device in devices
    ]


@router.get(
    "/me/my_devices",
    response_model=List[DeviceInDB],
    dependencies=[Depends(manager_and_superuser_permission_dependency)],
)
def get_all_devices_owned_by_current_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_currently_authenticated_user),
) -> List[DeviceInDB]:
    """
    This endpoint gives you all the devices which belong to the curent user.
    You need to be a superuser or an agent's manager to use this endpoint.
    """

    devices = device_repo.get_all_devices_with_agent_id(db, agent_id=current_user.agent_id)
    return [
        DeviceInDB(
            id=device.id,
            name=device.name,
            mac_id=device.mac_id,
            creator_id=device.creator_id,
            is_active=device.is_active,
            agent_id=device.agent_id,
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
        for device in devices
    ]


@router.get("/{mac_id}/metadata", response_model=DeviceMetaData)
def get_device_metadata(
    mac_id: str,
    *,
    db: Session = Depends(get_db),
    api_key: str = Security(DeviceAPIKeyHeader(name="X-API-KEY")),
):
    """
    This endpoint gets the config for the device with mac_id.
    You need an API Key in the header to use this endpoint.
    This API Key goes in the header like this X-API-Key: "<API-KEY>"
    If a device is inactive, you get a 403.
    """
    if API_KEY_AUTH_ENABLED and not api_key_repository.verify_api_key(
        db, plain_api_key=api_key
    ):
        raise UnauthorizedEndpointException(detail=INVALID_API_KEY)

    device = device_repo.get_by_field(db, field_name="mac_id", field_value=mac_id)
    if not device:
        raise ObjectNotFoundException(detail=f"device with mac_id {mac_id} not found")
    if not device.is_active:
        raise InactiveDeviceException()

    config = device_repo.get_device_config(db, device_obj=device)

    assigned_users = [
        assigned_user.to_json() for assigned_user in device.assigned_users
    ]
    device_agent = agent_repo.get(db, id=device.agent_id)

    config = DeviceConfig(**config)
    device_agent_json = device_agent.to_json()

    return DeviceMetaData(
        config=config,
        assigned_users=assigned_users,
        agent=device_agent_json,
    )


@router.put("/{mac_id}/device_users/{user_id}", response_model=DeviceUser)
def update_device_user(
    mac_id: str,
    user_id: int,
    *,
    db: Session = Depends(get_db),
    device_user_update_input: DeviceUserUpdate,
    api_key: str = Security(DeviceAPIKeyHeader(name="X-API-KEY")),
    background_tasks: BackgroundTasks,
):
    """
    This endpoint is used to update the details for the device user with user_id of user_id.
    The user must be assigned to the device with mac_id.
    Right now, the only field you can update of the device user is the password field
    You need an API Key in the header to use this endpoint.
    This API Key goes in the header like this X-API-Key: "<API-KEY>"
    """
    if API_KEY_AUTH_ENABLED and not api_key_repository.verify_api_key(
        db, plain_api_key=api_key
    ):
        raise UnauthorizedEndpointException(detail=INVALID_API_KEY)

    device = device_repo.get_by_field(db, field_name="mac_id", field_value=mac_id)
    if not device:
        raise ObjectNotFoundException(
            detail="device with mac id {} not found".format(mac_id)
        )

    device_user = user_repo.get(db, id=user_id)
    if not device_user:
        raise ObjectNotFoundException(
            detail="device user with id {} not found".format(user_id)
        )

    if device_user in device.assigned_users:
        device_user = user_repo.update(
            db, db_obj=device_user, obj_in={**device_user_update_input.dict()}
        )

        background_tasks.add_task(send_notification_to_devices, device.mac_id, " ")
        return DeviceUser(**device_user.to_json())

    raise UnauthorizedEndpointException()


@router.get("/{device_id}", response_model=DeviceInDB)
def get_device(
    device_id: int,
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_currently_authenticated_user),
):
    """
    This endpoint gets the device with device_id.
    The user can access this device on 3 conditions
    1. the user is a superuser
    2. the user created this device
    3. the user is currently assigned to the agent of the device

    """

    device = device_repo.get(db, id=device_id)

    if not device:
        raise ObjectNotFoundException()
    if (
        not can_access_device_obj(device, current_user)
        and device not in current_user.devices
    ):
        raise UnauthorizedEndpointException()
    return DeviceInDB(
        id=device.id,
        name=device.name,
        mac_id=device.mac_id,
        creator_id=device.creator_id,
        is_active=device.is_active,
        agent_id=device.agent_id,
        assigned_users=[
            SlimUserInResponse(
                id=user.id,
                email=user.email,
                lasrra_id=user.lasrra_id,
                user_type=UserTypeInDB(id=user.user_type.id, name=user.user_type.name),
            )
            for user in device.assigned_users
        ],
    )


@router.put("/{device_id}", response_model=DeviceInDB)
def update_device(
    device_id: int,
    *,
    db: Session = Depends(get_db),
    device_in: DeviceUpdate,
    current_user: User = Depends(get_currently_authenticated_user),
    background_tasks: BackgroundTasks,
):
    """
    This endpoint updates the device with device_id.
    The user can access this device on 3 conditions
    1. the user is a superuser
    2. the user created this device
    3. the user is currently assigned as the agent of the device
    """

    exists = device_repo.get_by_field(
        db, field_name="mac_id", field_value=device_in.mac_id
    )
    if exists:
        raise AlreadyExistsException(
            detail=ALREADY_EXISTS.format(f"device with mac id {device_in.mac_id}")
        )

    device = device_repo.get(db, id=device_id)

    if not device:
        raise ObjectNotFoundException()
    if not can_access_device_obj(device, current_user):
        raise UnauthorizedEndpointException()

    updated_device = device_repo.update(db, db_obj=device, obj_in=device_in)

    background_tasks.add_task(send_notification_to_devices, device.mac_id, " ")

    return DeviceInDB(
        id=updated_device.id,
        name=device.name,
        mac_id=updated_device.mac_id,
        creator_id=updated_device.creator_id,
        is_active=device.is_active,
        agent_id=device.agent_id,
        assigned_users=[
            SlimUserInResponse(
                id=user.id,
                email=user.email,
                lasrra_id=user.lasrra_id,
                user_type=UserTypeInDB(id=user.user_type.id, name=user.user_type.name),
            )
            for user in updated_device.assigned_users
        ],
    )


@router.delete("/{device_id}", response_model=DeviceInDB)
def delete_device(
    device_id: int,
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_currently_authenticated_user),
):
    device = device_repo.get(db, id=device_id)
    """
    This endpoint deletes the device with device_id. 
    The user can access this device on 3 conditions
    1. the user is a superuser
    2. the user created this device
    3. the user is currently assigned as the agent to the device
    """

    if not device:
        raise ObjectNotFoundException()
    if not can_access_device_obj(device, current_user):
        raise UnauthorizedEndpointException()

    deleted_device = device_repo.remove(db, id=device.id)

    return DeviceInDB(
        id=deleted_device.id,
        name=device.name,
        mac_id=deleted_device.mac_id,
        creator_id=deleted_device.creator_id,
        is_active=device.is_active,
        agent_id=device.agent_id,
        assigned_users=[
            SlimUserInResponse(
                id=user.id,
                email=user.email,
                lasrra_id=user.lasrra_id,
                user_type=UserTypeInDB(id=user.user_type.id, name=user.user_type.name),
            )
            for user in deleted_device.assigned_users
        ],
    )


@router.post(
    "/activate/{device_id}",
    response_model=DeviceInDB,
    dependencies=[Depends( manager_and_supervisor_and_superuser_permission_dependency,)],
)
def activate_device(
    device_id: int,
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_currently_authenticated_user),
    background_tasks: BackgroundTasks,
):
    """
    This endpoint allows you to activate a device. <br/> You've to be a superuser to use this endpoint.
    """
    device = device_repo.get(db, id=device_id)

    if not device:
        raise ObjectNotFoundException()
    if not can_access_device_obj(device, current_user):
        raise UnauthorizedEndpointException()

    updated_device = device_repo.activate_device(db, device_obj=device)

    template_dict = DeviceActivationTemplateVariables(
        name=f"{current_user.first_name} {current_user.last_name}", mac_id=device.mac_id
    ).dict()

    background_tasks.add_task(
        send_email_with_template,
        client=core.PostmarkClient(server_token=settings.POSTMARK_API_TOKEN),
        template_id=ACTIVATE_DEVICE_TEMPLATE_ID,
        template_dict=template_dict,
        recipient=current_user.email,
    )

    background_tasks.add_task(send_notification_to_devices, device.mac_id, " ")

    return DeviceInDB(
        id=updated_device.id,
        name=device.name,
        mac_id=updated_device.mac_id,
        creator_id=updated_device.creator_id,
        is_active=updated_device.is_active,
        agent_id=device.agent_id,
        assigned_users=[
            SlimUserInResponse(
                id=user.id,
                email=user.email,
                lasrra_id=user.lasrra_id,
                user_type=UserTypeInDB(id=user.user_type.id, name=user.user_type.name),
            )
            for user in updated_device.assigned_users
        ],
    )


@router.post(
    "/deactivate/{device_id}",
    response_model=DeviceInDB,
    dependencies=[Depends( manager_and_supervisor_and_superuser_permission_dependency)],
)
def deactivate_device(
    device_id: int,
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_currently_authenticated_user),
    background_tasks: BackgroundTasks,
):
    """
    This endpoint allows you to deactivate a device. <br/> You've to be a superuser to use this endpoint.
    """
    device = device_repo.get(db, id=device_id)

    if not device:
        raise ObjectNotFoundException()
    if not can_access_device_obj(device, current_user):
        raise UnauthorizedEndpointException()

    updated_device = device_repo.deactivate_device(db, device_obj=device)

    template_dict = DeviceDeactivationTemplateVariables(
        name=f"{current_user.first_name} {current_user.last_name}", mac_id=device.mac_id
    ).dict()

    background_tasks.add_task(
        send_email_with_template,
        client=core.PostmarkClient(server_token=settings.POSTMARK_API_TOKEN),
        template_id=DEACTIVATE_DEVICE_TEMPLATE_ID,
        template_dict=template_dict,
        recipient=current_user.email,
    )

    background_tasks.add_task(send_notification_to_devices, device.mac_id, " ")

    return DeviceInDB(
        id=updated_device.id,
        name=device.name,
        mac_id=updated_device.mac_id,
        creator_id=updated_device.creator_id,
        is_active=device.is_active,
        agent_id=device.agent_id,
        assigned_users=[
            SlimUserInResponse(
                id=user.id,
                email=user.email,
                lasrra_id=user.lasrra_id,
                user_type=UserTypeInDB(id=user.user_type.id, name=user.user_type.name),
            )
            for user in updated_device.assigned_users
        ],
    )


@router.post(
    "/assign/{device_id}/{user_id}",
    dependencies=[Depends(manager_and_supervisor_and_superuser_permission_dependency)],
)
def assign_device(
    device_id: int,
    user_id: int,
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_currently_authenticated_user),
    background_tasks: BackgroundTasks,
):
    """
    This endpoint assigns the device with device_id to the given user_id.
    The given user_id has to be an agent employee, you can not assign non-agent employees to devices.
    You need to be a superuser or an manager to perform this action
    """
    device = device_repo.get(db, id=device_id)
    user = user_repo.get(db, id=user_id)

    if not device or not user:
        detail = (
            f"device with id {device_id} not found"
            if not device
            else f"user with id {user_id} not found"
        )
        raise ObjectNotFoundException(detail=detail)

    if user.user_type.name != AGENT_OFFICER:
        raise UnauthorizedEndpointException(detail=NOT_AN_AGENT_OFFICER_ERROR,)

    if not can_access_device_obj(device, current_user):
        raise UnauthorizedEndpointException()

    if not device.is_active:
        raise InactiveDeviceException()

    updated_device = device_repo.add_assigned_user(db, device_obj=device, user_obj=user)

    background_tasks.add_task(send_notification_to_devices, device.mac_id, " ")

    return DeviceInDB(
        id=updated_device.id,
        name=device.name,
        mac_id=updated_device.mac_id,
        creator_id=updated_device.creator_id,
        is_active=updated_device.is_active,
        agent_id=updated_device.agent_id,
        assigned_users=[
            SlimUserInResponse(
                id=user.id,
                email=user.email,
                lasrra_id=user.lasrra_id,
                user_type=UserTypeInDB(id=user.user_type.id, name=user.user_type.name),
            )
            for user in updated_device.assigned_users
        ],
    )


@router.post(
    "/unassign/{device_id}/{user_id}",
    dependencies=[Depends( manager_and_supervisor_and_superuser_permission_dependency)],
)
def unassign_device_from_user(
    user_id: int,
    device_id: int,
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_currently_authenticated_user),
    background_tasks: BackgroundTasks,
):
    """
    This endpoint unassigns the device with device_id from the given user_id.
    You need to be a superuser or an agent's manager to perform this action
    """
    device = device_repo.get(db, id=device_id)
    user = user_repo.get(db, id=user_id)

    if not device:
        raise ObjectNotFoundException(detail=f"device with id {device_id} not found")
    if not user:
        raise ObjectNotFoundException(detail=f"user with id {user_id} not found")

    if not can_access_device_obj(device, current_user):
        raise UnauthorizedEndpointException()

    updated_device = device_repo.remove_assigned_user(
        db, device_obj=device, user_obj=user
    )

    background_tasks.add_task(send_notification_to_devices, device.mac_id, " ")

    return DeviceInDB(
        id=updated_device.id,
        name=device.name,
        mac_id=updated_device.mac_id,
        creator_id=updated_device.creator_id,
        is_active=device.is_active,
        agent_id=device.agent_id,
        assigned_users=[
            SlimUserInResponse(
                id=user.id,
                email=user.email,
                lasrra_id=user.lasrra_id,
                user_type=UserTypeInDB(id=user.user_type.id, name=user.user_type.name),
            )
            for user in updated_device.assigned_users
        ],
    )


@router.get("/assigned/{user_id}", response_model=List[DeviceInDB])
def get_all_devices_assigned_to_user_with_user_id(
    user_id: int,
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_currently_authenticated_user),
) -> List[DeviceInDB]:
    """
    This endpoint gets all the devices which are assigned to the user with
    the given user_id.
    You need to be a superuser, or the creator of the user with user_id
    or the user with id == user_id themself.
    """
    user = user_repo.get(db, id=user_id)
    if not user:
        raise ObjectNotFoundException()

    if (
        current_user.id != user_id
        and current_user.user_type.name != SUPERUSER_USER_TYPE
        and user.created_by_id != current_user.id
    ):
        raise UnauthorizedEndpointException()

    devices = user_repo.get_all_devices_assigned_to_user_with_user_id(
        db, user_id=user_id
    )

    return [
        DeviceInDB(
            id=device.id,
            name=device.name,
            mac_id=device.mac_id,
            creator_id=device.creator_id,
            is_active=device.is_active,
            agent_id=device.agent_id,
            assigned_users=[
                SlimUserInResponse(
                    id=user.id,
                    email=user.email,
                    lasrra_id=user.lasrra_id,
                    user_type=UserTypeInDB(
                        id=user.user_type.id, name=user.user_type.name
                    ),
                    created_by_id=current_user.id,
                )
                for user in device.assigned_users
            ],
        )
        for device in devices
    ]




@router.post(
    "/{device_id}/allocate_to_agent/{agent_user_id}",
    response_model=DeviceInDB,
    dependencies=[Depends(superuser_permission_dependency)],
)
def allocate_device_to_agent(
    device_id: int,
    agent_user_id: int,
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_currently_authenticated_user),
) -> DeviceInDB:
    """
    This endpoints allocates a device with device id device_id to an agent with user_id of agent_user_id.
    This is different from simplying assigning devices to agent employees.
    You need to be a superuser to use this endpoint
    """
    agent_user = user_repo.get(db, id=agent_user_id)
    device = device_repo.get(db, id=device_id)

    if not device or not agent_user:
        error_prefix = (
            "device with id {}".format(device_id)
            if not device
            else "agent with id {}".format(agent_user_id)
        )
        raise ObjectNotFoundException(detail=error_prefix + " " + NOT_FOUND)
    if not agent_user.user_type.name == AGENT:
        raise HTTPException(HTTP_403_FORBIDDEN, detail=NOT_AN_AGENT_ERROR)

    device.agent_id = agent_user.id
    device = device_repo.update(db, db_obj=device, obj_in={})

    return DeviceInDB(
        id=device.id,
        name=device.name,
        mac_id=device.mac_id,
        creator_id=device.creator_id,
        is_active=device.is_active,
        agent_id=device.agent_id,
        assigned_users=[
            SlimUserInResponse(
                id=user.id,
                email=user.email,
                lasrra_id=user.lasrra_id,
                user_type=UserTypeInDB(id=user.user_type.id, name=user.user_type.name),
                created_by_id=current_user.id,
            )
            for user in device.assigned_users
        ],
    )
