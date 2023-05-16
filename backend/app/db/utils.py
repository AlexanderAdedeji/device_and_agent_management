from backend.app.core.settings import settings
from backend.app.db import session
from backend.app.db.repositories.user import user_repo
from backend.app.db.repositories.agent import agent_repo
from backend.app.db.repositories.user_type import user_type as user_type_repository
from backend.app.models.user import User
from backend.app.schemas import UserCreate, UserTypeCreate
from backend.app.schemas.agent import (
    Agent,
    AgentCreate,
    AgentCreateForm,
    AgentUpdate,
    AgentProfile,
    AgentInResponse
)
from fastapi import FastAPI
from loguru import logger
from sqlalchemy.orm import Session

# AGENT_EMPLOYEE_TYPE = settings.AGENT_EMPLOYEE_TYPE
AGENT = settings.AGENT
AGENT_MANAGER= settings.AGENT_MANAGER
AGENT_OFFICER= settings.AGENT_OFFICER
AGENT_SUPERVISOR= settings.AGENT_SUPERVISOR

API_URL_PREFIX = settings.API_URL_PREFIX
# Agent = settings.Agent
# AgentEmployeeUser = settings.AgentEmployeeUser
AgentSupervisorUser = settings.AgentSupervisorUser
AgentManagerUser = settings.AgentManagerUser
AgentOfficerUser = settings.AgentOfficerUser
DATABASE_URI = settings.DATABASE_URI
FIRST_SUPERUSER_ADDRESS = settings.FIRST_SUPERUSER_ADDRESS
FIRST_SUPERUSER_EMAIL = settings.FIRST_SUPERUSER_EMAIL
FIRST_SUPERUSER_FIRSTNAME = settings.FIRST_SUPERUSER_FIRSTNAME
FIRST_SUPERUSER_LASSRA_ID = settings.FIRST_SUPERUSER_LASSRA_ID
FIRST_SUPERUSER_LASTNAME = settings.FIRST_SUPERUSER_LASTNAME
FIRST_SUPERUSER_PASSWORD = settings.FIRST_SUPERUSER_PASSWORD
FIRST_SUPERUSER_PHONE = settings.FIRST_SUPERUSER_PHONE
SecondSuperUser = settings.SecondSuperUser
SUPERUSER_USER_TYPE = settings.SUPERUSER_USER_TYPE
USER_TYPES = settings.USER_TYPES


class DataInitializer:
    def __init__(self, db: Session, skip_auto_initialization=False):
        self.db = db
        self.user_types_have_been_created = False
        # Order of being called is important as existence of one model depends on the other

        if not skip_auto_initialization:
            self.create_user_types()
            # self.create_default_agents()
            self.create_default_superusers()
           
            # self.create_default_agent_employees()
            self.create_default_manager()
            self.create_default_supervisor()
            self.create_default_agent_officers()
            

    def _create_user_type(self, type_name: str):
        new_type = UserTypeCreate(name=type_name)
        user_type_repository.create(self.db, obj_in=new_type)

    def create_user_types(self):
        db = self.db
        for _, user_type_name in USER_TYPES.items():
            user_type = user_type_repository.get_by_name(db, name=user_type_name)
            if not user_type:
                self._create_user_type(user_type_name)

        self.user_types_have_been_created = True

    # def create_default_agents(self):
    #     db = self.db
    #     assert self.user_types_have_been_created
    #     user_type = user_type_repository.get_by_name(db, name=AGENT)
    #     assert user_type

    #     self._create_default_agents(
    #         AgentCreate(
    #             name=settings.Agent.NAME,       
    #             address=settings.Agent.ADDRESS,      
    #             email=settings.Agent.EMAIL,
    #             user_type_id=user_type.id,
    #         )
    #     )



    def create_default_supervisor(self):
        db = self.db
        assert self.user_types_have_been_created
        user_type = user_type_repository.get_by_name(db, name=AGENT_SUPERVISOR)
        assert user_type

        self._create_default_user(
            UserCreate(
                first_name=AgentSupervisorUser.FIRSTNAME,
                last_name=AgentSupervisorUser.LASTNAME,
                address=AgentSupervisorUser.ADDRESS,
                phone=AgentSupervisorUser.PHONE,
                email=AgentSupervisorUser.EMAIL,
                password=AgentSupervisorUser.PASSWORD,
                lasrra_id=AgentSupervisorUser.LASSRA_ID,
                user_type_id=user_type.id,
            )
        )
        
    def create_default_manager(self):
        db = self.db
        assert self.user_types_have_been_created
        user_type = user_type_repository.get_by_name(db, name=AGENT_MANAGER)
        assert user_type

        self._create_default_user(
            UserCreate(
                first_name=AgentManagerUser.FIRSTNAME,
                last_name=AgentManagerUser.LASTNAME,
                address=AgentManagerUser.ADDRESS,
                phone=AgentManagerUser.PHONE,
                email=AgentManagerUser.EMAIL,
                password=AgentManagerUser.PASSWORD,
                lasrra_id=AgentManagerUser.LASSRA_ID,
                user_type_id=user_type.id,
            )
        )



    
    def create_default_agent_officers(self):
        db = self.db
        assert self.user_types_have_been_created
        user_type = user_type_repository.get_by_name(db, name=AGENT_OFFICER)
        assert user_type

        self._create_default_user(
            UserCreate(
                first_name=AgentOfficerUser.FIRSTNAME,
                last_name=AgentOfficerUser.LASTNAME,
                address=AgentOfficerUser.ADDRESS,
                phone=AgentOfficerUser.PHONE,
                email=AgentOfficerUser.EMAIL,
                password=AgentOfficerUser.PASSWORD,
                lasrra_id=AgentOfficerUser.LASSRA_ID,
                user_type_id=user_type.id,
            )
        )

        # def create_default_agent_employees(self):
        #     db = self.db
        # assert self.user_types_have_been_created
        # user_type = user_type_repository.get_by_name(db, name=AGENT_EMPLOYEE_TYPE)
        # assert user_type

        # self._create_default_user(
        #     UserCreate(
        #         first_name=AgentEmployeeUser.FIRSTNAME,
        #         last_name=AgentEmployeeUser.LASTNAME,
        #         address=AgentEmployeeUser.ADDRESS,
        #         phone=AgentEmployeeUser.PHONE,
        #         email=AgentEmployeeUser.EMAIL,
        #         password=AgentEmployeeUser.PASSWORD,
        #         lasrra_id=AgentEmployeeUser.LASSRA_ID,
        #         user_type_id=user_type.id,
        #     )
        # )

    def _create_default_user(self, user_in: UserCreate) -> User:
        db = self.db
        user = user_repo.get_by_email(db, email=user_in.email)
        if not user:
            user = user_repo.create(db, obj_in=user_in)
            user_repo.activate(db, db_obj=user)
        return user

    def _create_default_agents(self, agent_in: AgentCreate) -> Agent:
        db = self.db
        agent = agent_repo.get_by_email(db, email=agent_in.email)
        if not agent:
            agent = agent_repo.create(db, obj_in=agent_in)
            # agent_repo.activate(db, db_obj=agent)
        return agent

    def create_default_superusers(self):
        db = self.db
        assert self.user_types_have_been_created
        user_type = user_type_repository.get_by_name(db, name=SUPERUSER_USER_TYPE)
        assert user_type

        self._create_superuser(
            user_in=UserCreate(
                first_name=FIRST_SUPERUSER_FIRSTNAME,
                last_name=FIRST_SUPERUSER_LASTNAME,
                address=FIRST_SUPERUSER_ADDRESS,
                phone=FIRST_SUPERUSER_PHONE,
                email=FIRST_SUPERUSER_EMAIL,
                password=FIRST_SUPERUSER_PASSWORD,
                lasrra_id=FIRST_SUPERUSER_LASSRA_ID,
                user_type_id=user_type.id,
            )
        )

        self._create_superuser(
            user_in=UserCreate(
                first_name=SecondSuperUser.FIRSTNAME,
                last_name=SecondSuperUser.LASTNAME,
                address=SecondSuperUser.ADDRESS,
                phone=SecondSuperUser.PHONE,
                email=SecondSuperUser.EMAIL,
                password=SecondSuperUser.PASSWORD,
                lasrra_id=SecondSuperUser.LASSRA_ID,
                user_type_id=user_type.id,
            )
        )

    def _create_superuser(self, user_in: UserCreate):
        user = self._create_default_user(user_in=user_in)
        user_repo.update(self.db, db_obj=user, obj_in={"is_superuser": True})


async def connect_to_db(app: FastAPI) -> None:
    logger.info("Initializing DB")

    DataInitializer(session.SessionLocal())

    logger.info("DB initialized")


def build_custom_regex_pattern(
    pattern: str,
):
    if pattern[0] == "^":
        pattern = pattern[1:]
    pattern = "^" + API_URL_PREFIX + pattern
    return pattern


async def close_db_connection(app: FastAPI) -> None:
    logger.info("Closing connection to database")

    # await app.state.pool.close()

    logger.info("Connection closed")
