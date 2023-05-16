from starlette.status import HTTP_403_FORBIDDEN
from backend.app.models.user_type import UserType
from typing import List, Optional

from backend.app.api.dependencies.db import get_db
from backend.app.api.errors.error_strings import (
    AUTHENTICATION_REQUIRED,
    INACTIVE_USER_ERROR,
    INVALID_API_KEY,
    MALFORMED_PAYLOAD,
    WRONG_TOKEN_PREFIX,
)
from backend.app.api.errors.exceptions import (
    DisallowedLoginException,
    InvalidTokenException,
    UnauthorizedEndpointException,
)
from backend.app.core.settings import settings
from backend.app.models import User
from backend.app.db.repositories.user import user_repo
from backend.app.db.repositories.api_key import api_key_repository
from backend.app.services.jwt import get_id_from_token
from fastapi import Depends, HTTPException, Security
from fastapi.security import (
    APIKeyHeader as DefaultAPIKeyHeader,
)
from loguru import logger
from sqlalchemy.orm import Session
from starlette import requests
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.api.errors import error_strings

JWT_TOKEN_PREFIX = settings.JWT_TOKEN_PREFIX
HEADER_KEY = settings.HEADER_KEY

AGENT = settings.AGENT
SUPERUSER_USER_TYPE = settings.SUPERUSER_USER_TYPE
AGENT_SUPERVISOR_USER_TYPE =settings.AGENT_SUPERVISOR
AGENT_MANAGER_USER_TYPE = settings.AGENT_MANAGER


class DeviceAPIKeyHeader(DefaultAPIKeyHeader):
    async def __call__(
        self,
        request: requests.Request,
    ) -> Optional[str]:
        try:
            return await super().__call__(request)
        except StarletteHTTPException as original_auth_exc:
            raise HTTPException(
                status_code=original_auth_exc.status_code,
                detail=INVALID_API_KEY,
            )


class JWTHeader(DefaultAPIKeyHeader):
    async def __call__(
        _,
        request: requests.Request,
    ) -> Optional[str]:
        try:
            return await super().__call__(request)
        except StarletteHTTPException as original_auth_exc:
            raise HTTPException(
                status_code=original_auth_exc.status_code,
                detail=original_auth_exc.detail or AUTHENTICATION_REQUIRED,
            )


def _extract_jwt_from_header(
    authorization_header: str = Security(JWTHeader(name=HEADER_KEY)),
) -> str:
    try:
        token_prefix, token = authorization_header.split(" ")
    except ValueError:
        raise InvalidTokenException(detail=WRONG_TOKEN_PREFIX)

    if token_prefix != JWT_TOKEN_PREFIX:
        raise InvalidTokenException(detail=WRONG_TOKEN_PREFIX)
    return token


def get_currently_authenticated_user(
    *,
    db: Session = Depends(get_db),
    token: str = Depends(_extract_jwt_from_header),
) -> User:
    try:
        id = get_id_from_token(token)
        user = user_repo.get(db, id=id)
        check_if_user_is_valid(user)
    except ValueError:
        raise InvalidTokenException(detail=MALFORMED_PAYLOAD)
    return user


def check_if_user_is_valid(user: User):
    if not user:
        raise InvalidTokenException(detail=MALFORMED_PAYLOAD)
    if not user.is_active:
        raise DisallowedLoginException(detail=INACTIVE_USER_ERROR)


class PermissionChecker:
    def __init__(self, *, allowed_user_types: List[str]):
        self.allowed_user_types = allowed_user_types

    def __call__(self, user: User = Depends(get_currently_authenticated_user)):
        current_user_type: UserType = user.user_type
        if current_user_type.name not in self.allowed_user_types:
            logger.debug(
                f"User with type {current_user_type.name} not in {self.allowed_user_types}"
            )
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN, detail=error_strings.UNAUTHORIZED_ACTION
            )


manager_and_superuser_permission_dependency = PermissionChecker(
    allowed_user_types=[AGENT_MANAGER_USER_TYPE, SUPERUSER_USER_TYPE]
)

manager_and_supervisor_and_superuser_permission_dependency = PermissionChecker(
    allowed_user_types=[SUPERUSER_USER_TYPE, AGENT_MANAGER_USER_TYPE, AGENT_SUPERVISOR_USER_TYPE]
)

superuser_permission_dependency = PermissionChecker(
    allowed_user_types=[SUPERUSER_USER_TYPE]
)