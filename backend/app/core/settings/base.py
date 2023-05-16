import collections
import os
from pathlib import Path
from typing import Any
from pydantic import BaseSettings, EmailStr, validator
from pydantic.networks import EmailStr
from starlette.datastructures import CommaSeparatedStrings


class CustomBaseSettings(BaseSettings):

    ALLOWED_HOSTS: Any
    DATABASE_URI: str
    SECRET_KEY: str
    RESET_TOKEN_EXPIRE_MINUTES: int = 60
    PROJECT_NAME: str = "Device Agent Mgmt Server"

    API_URL_PREFIX: str
    JWT_TOKEN_PREFIX: str = "Token"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7
    JWT_ALGORITHM: str = "HS256"
    HEADER_KEY: str = "Authorization"
    API_KEY_AUTH_ENABLED: bool = True
    VERSION: str = "0.1.0"
    DEBUG: bool = False

    FIRST_SUPERUSER_EMAIL: EmailStr
    FIRST_SUPERUSER_PASSWORD: str
    FIRST_SUPERUSER_FIRSTNAME: str
    FIRST_SUPERUSER_LASTNAME: str
    FIRST_SUPERUSER_PHONE: str
    FIRST_SUPERUSER_LASSRA_ID: str
    FIRST_SUPERUSER_ADDRESS: str

    SECOND_SUPERUSER_EMAIL: EmailStr
    SECOND_SUPERUSER_PASSWORD: str
    SECOND_SUPERUSER_FIRSTNAME: str
    SECOND_SUPERUSER_LASTNAME: str
    SECOND_SUPERUSER_PHONE: str
    SECOND_SUPERUSER_LASSRA_ID: str
    SECOND_SUPERUSER_ADDRESS: str

    FIRST_AGENT_EMAIL:EmailStr
    FIRST_AGENT_NAME:str
    FIRST_AGENT_ADDRESS:str


    FIRST_AGENT_MANAGER_EMAIL: EmailStr
    FIRST_AGENT_MANAGER_PASSWORD: str
    FIRST_AGENT_MANAGER_FIRSTNAME: str
    FIRST_AGENT_MANAGER_LASTNAME: str
    FIRST_AGENT_MANAGER_PHONE: str
    FIRST_AGENT_MANAGER_LASSRA_ID: str
    FIRST_AGENT_MANAGER_ADDRESS: str

    # SECOND_MANAGER_EMAIL: EmailStr
    # SECOND_MANAGER_PASSWORD: str
    # SECOND_MANAGER_FIRSTNAME: str
    # SECOND_MANAGER_LASTNAME: str
    # SECOND_MANAGER_PHONE: str
    # SECOND_MANAGER_LASSRA_ID: str
    # SECOND_MANAGER_ADDRESS: str

    FIRST_AGENT_SUPERVISOR_EMAIL: EmailStr
    FIRST_AGENT_SUPERVISOR_PASSWORD: str
    FIRST_AGENT_SUPERVISOR_FIRSTNAME: str
    FIRST_AGENT_SUPERVISOR_LASTNAME: str
    FIRST_AGENT_SUPERVISOR_PHONE: str
    FIRST_AGENT_SUPERVISOR_LASSRA_ID: str
    FIRST_AGENT_SUPERVISOR_ADDRESS: str

    # SECOND_SUPERVISOR_EMAIL: EmailStr
    # SECOND_SUPERVISOR_PASSWORD: str
    # SECOND_SUPERVISOR_FIRSTNAME: str
    # SECOND_SUPERVISOR_LASTNAME: str
    # SECOND_SUPERVISOR_PHONE: str
    # SECOND_SUPERVISOR_LASSRA_ID: str
    # SECOND_SUPERVISOR_ADDRESS: str


    FIRST_AGENT_OFFICER_EMAIL: EmailStr
    FIRST_AGENT_OFFICER_PASSWORD: str
    FIRST_AGENT_OFFICER_FIRSTNAME: str
    FIRST_AGENT_OFFICER_LASTNAME: str
    FIRST_AGENT_OFFICER_PHONE: str
    FIRST_AGENT_OFFICER_LASSRA_ID: str
    FIRST_AGENT_OFFICER_ADDRESS: str

    # SECOND_OFFICER_EMAIL: EmailStr
    # SECOND_OFFICER_PASSWORD: str
    # SECOND_OFFICER_FIRSTNAME: str
    # SECOND_OFFICER_LASTNAME: str
    # SECOND_OFFICER_PHONE: str
    # SECOND_OFFICER_LASSRA_ID: str
    # SECOND_OFFICER_ADDRESS: str


    # FIRST_AGENT_EMPLOYEE_EMAIL: str
    # FIRST_AGENT_EMPLOYEE_PASSWORD: str
    # FIRST_AGENT_EMPLOYEE_FIRSTNAME: str
    # FIRST_AGENT_EMPLOYEE_LASTNAME: str
    # FIRST_AGENT_EMPLOYEE_PHONE: str
    # FIRST_AGENT_EMPLOYEE_LASSRA_ID: str
    # FIRST_AGENT_EMPLOYEE_ADDRESS: str

    @validator("ALLOWED_HOSTS", always=True)
    def parse_allowed_hosts(cls, v, values, **kwargs):
        return str(CommaSeparatedStrings(v)).split(",")

    REGULAR_USER_TYPE = "REGULAR"
    SUPERUSER_USER_TYPE = "SUPERUSER"
    AGENT = "AGENT"
    AGENT_MANAGER = "AGENT_MANAGER"
    AGENT_SUPERVISOR = "AGENT_SUPERVISOR"
    # AGENT_EMPLOYEE_TYPE = "AGENT_EMPLOYEE_TYPE"
    AGENT_OFFICER = "AGENT_OFFICER"


    USER_TYPES = collections.defaultdict(lambda: REGULAR_USER_TYPE)

    USER_TYPES[REGULAR_USER_TYPE] = REGULAR_USER_TYPE
    USER_TYPES[SUPERUSER_USER_TYPE] = SUPERUSER_USER_TYPE
    USER_TYPES[AGENT] = AGENT
    USER_TYPES[AGENT_MANAGER] = AGENT_MANAGER
    USER_TYPES[AGENT_SUPERVISOR] = AGENT_SUPERVISOR
    USER_TYPES[AGENT_OFFICER] = AGENT_OFFICER
    # USER_TYPES[AGENT_EMPLOYEE_TYPE] = AGENT_EMPLOYEE_TYPE

    RESET_PASSWORD_URL: str

    POSTMARK_API_TOKEN: str
    DEFAULT_EMAIL_SENDER: EmailStr
    RESET_PASSWORD_TEMPLATE_ID: int
    ACTIVATE_ACCOUNT_TEMPLATE_ID: int
    DEACTIVATE_ACCOUNT_TEMPLATE_ID: int
    CREATE_ACCOUNT_TEMPLATE_ID: int
    ACTIVATE_DEVICE_TEMPLATE_ID: int
    DEACTIVATE_DEVICE_TEMPLATE_ID: int

    RABBIT_MQ_URI: str
    EXTERNAL_RABBIT_MQ_URI: str

    RESET_PASSWORD_URL: str

    API_BASE_URL: str



    # class AgentEmployeeUser:
    #     EMAIL: str
    #     PASSWORD: str
    #     FIRSTNAME: str
    #     LASTNAME: str
    #     PHONE: str
    #     LASSRA_ID: str
    #     ADDRESS: str

    class Agent:
        EMAIL: EmailStr
        NAME: str
        ADDRESS: str

        
    class AgentManagerUser:
        EMAIL: str
        PASSWORD: str
        FIRSTNAME: str
        LASTNAME: str
        PHONE: str
        LASSRA_ID: str
        ADDRESS: str

        
        
    class AgentOfficerUser:
        EMAIL: str
        PASSWORD: str
        FIRSTNAME: str
        LASTNAME: str
        PHONE: str
        LASSRA_ID: str
        ADDRESS: str


    class AgentSupervisorUser:
        EMAIL: str
        PASSWORD: str
        FIRSTNAME: str
        LASTNAME: str
        PHONE: str
        LASSRA_ID: str
        ADDRESS: str

    class SecondSuperUser:
        EMAIL: str
        PASSWORD: str
        FIRSTNAME: str
        LASTNAME: str
        PHONE: str
        LASSRA_ID: str
        ADDRESS: str

    class Config:
        env_file = os.getenv(
            "ENV_VARIABLE_PATH", Path(__file__).parent / "env_files" / ".env"
        )
