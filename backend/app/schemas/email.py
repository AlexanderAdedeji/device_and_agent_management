from pydantic import BaseModel
from typing import Any, Dict, Optional
from backend.app.core.settings import settings


class Email(BaseModel):
    template_id: str
    template_dict: str
    recipient: str
    sender: str


class EmailCreate(Email):
    pass


class EmailUpdate(BaseModel):
    delivered: bool
    extra_data: Optional[str]


class EmailTemplateVariables(BaseModel):
    name: str


class ResetPasswordEmailTemplateVariables(EmailTemplateVariables):
    reset_link: str
    valid_for: Optional[int] = settings.RESET_TOKEN_EXPIRE_MINUTES // 60


class DeviceActivationTemplateVariables(EmailTemplateVariables):
    mac_id: str


class DeviceDeactivationTemplateVariables(EmailTemplateVariables):
    mac_id: str


class UserActivationTemplateVariables(EmailTemplateVariables):
    pass


class UserDeactivationTemplateVariables(EmailTemplateVariables):
    pass


class UserCreationTemplateVariables(EmailTemplateVariables):
    pass


class AgentCreationTemplateVariable(EmailTemplateVariables):
    pass
