import logging
import sys

from backend.app.core.settings.base import CustomBaseSettings
from backend.app.core.settings.production import ProductionSettings

from backend.app.core.logging import InterceptHandler
from backend.app.core.settings.local import LocalSettings
from loguru import logger

if CustomBaseSettings().DEBUG:
    settings = LocalSettings()
else:
    settings = ProductionSettings()


settings.Agent.Name = settings.FIRST_AGENT_NAME
settings.Agent.Email = settings.FIRST_AGENT_EMAIL
settings.Agent.ADDRESS = settings.FIRST_AGENT_ADDRESS



settings.AgentManagerUser.EMAIL = settings.FIRST_AGENT_MANAGER_EMAIL
settings.AgentManagerUser.PASSWORD = settings.FIRST_AGENT_MANAGER_PASSWORD
settings.AgentManagerUser.FIRSTNAME = settings.FIRST_AGENT_MANAGER_FIRSTNAME
settings.AgentManagerUser.LASTNAME = settings.FIRST_AGENT_MANAGER_LASTNAME
settings.AgentManagerUser.PHONE = settings.FIRST_AGENT_MANAGER_PHONE
settings.AgentManagerUser.LASSRA_ID = settings.FIRST_AGENT_MANAGER_LASSRA_ID
settings.AgentManagerUser.ADDRESS = settings.FIRST_AGENT_MANAGER_ADDRESS

settings.AgentOfficerUser.EMAIL = settings.FIRST_AGENT_OFFICER_EMAIL
settings.AgentOfficerUser.PASSWORD = settings.FIRST_AGENT_OFFICER_PASSWORD
settings.AgentOfficerUser.FIRSTNAME = settings.FIRST_AGENT_OFFICER_FIRSTNAME
settings.AgentOfficerUser.LASTNAME = settings.FIRST_AGENT_OFFICER_LASTNAME
settings.AgentOfficerUser.PHONE = settings.FIRST_AGENT_OFFICER_PHONE
settings.AgentOfficerUser.LASSRA_ID = settings.FIRST_AGENT_OFFICER_LASSRA_ID
settings.AgentOfficerUser.ADDRESS = settings.FIRST_AGENT_OFFICER_ADDRESS


settings.AgentSupervisorUser.EMAIL = settings.FIRST_AGENT_SUPERVISOR_EMAIL
settings.AgentSupervisorUser.PASSWORD = settings.FIRST_AGENT_SUPERVISOR_PASSWORD
settings.AgentSupervisorUser.FIRSTNAME = settings.FIRST_AGENT_SUPERVISOR_FIRSTNAME
settings.AgentSupervisorUser.LASTNAME = settings.FIRST_AGENT_SUPERVISOR_LASTNAME
settings.AgentSupervisorUser.PHONE = settings.FIRST_AGENT_SUPERVISOR_PHONE
settings.AgentSupervisorUser.LASSRA_ID = settings.FIRST_AGENT_SUPERVISOR_LASSRA_ID
settings.AgentSupervisorUser.ADDRESS = settings.FIRST_AGENT_SUPERVISOR_ADDRESS



settings.SecondSuperUser.EMAIL = settings.SECOND_SUPERUSER_EMAIL
settings.SecondSuperUser.PASSWORD = settings.SECOND_SUPERUSER_PASSWORD
settings.SecondSuperUser.FIRSTNAME = settings.SECOND_SUPERUSER_FIRSTNAME
settings.SecondSuperUser.LASTNAME = settings.SECOND_SUPERUSER_LASTNAME
settings.SecondSuperUser.PHONE = settings.SECOND_SUPERUSER_PHONE
settings.SecondSuperUser.LASSRA_ID = settings.SECOND_SUPERUSER_LASSRA_ID
settings.SecondSuperUser.ADDRESS = settings.SECOND_SUPERUSER_ADDRESS


LOGGING_LEVEL = logging.DEBUG if settings.DEBUG else logging.INFO
LOGGERS = ("uvicorn.asgi", "uvicorn.access")

logging.getLogger().handlers = [InterceptHandler()]
for logger_name in LOGGERS:
    logging_logger = logging.getLogger(logger_name)
    logging_logger.handlers = [InterceptHandler(level=LOGGING_LEVEL)]

logger.configure(handlers=[{"sink": sys.stderr, "level": LOGGING_LEVEL}])
