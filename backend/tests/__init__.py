# from operator import pos
# from os import environ
# from testcontainers.postgres import PostgresContainer
# from sqlalchemy import create_engine

# postgres = PostgresContainer()
# postgres.start()

# environ["TEST_DB_URL"] = postgres.get_connection_url()

# from backend.app.db.base import Base
# from sqlalchemy.orm import sessionmaker
# from backend.app.db.utils import DataInitializer

# engine = create_engine(postgres.get_connection_url())
# Base.metadata.create_all(engine)
# session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# DataInitializer(session())
