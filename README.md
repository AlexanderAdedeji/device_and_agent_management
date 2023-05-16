# Device & Agent Management System

## Cloning the repo
This project has a submodule for some common code between the client repo (desktop application) and this backend. Hence, you need to include the --recurse-submodules argument while cloning so git knows to get the submodules appropriately.

```
git clone --recurse-submodules <repo_uri>
```

## Installing Dependencies
The application uses [poetry](https:/python-poetry.org/) to manage dependencies.
Poetry helps you with managing dependencies within virtual environments.

After installing poetry, simply run `poetry shell` to create a virtual env and `poetry install` to install all dependencies

## Creating .env files
There are 3 places you need to set up .env files. These places always have an accompanying .env.example to indicate all the keys required within the .env file

1. The root directory .env file - This contains configuration for the database like postgres & mongo and also the rabbit mq configuration

2. ./worker/.env - This contains configuration for the worker. It has the mongo db name & credentials in which the worker stores logs as well as rabbit mq uri's and exchange names

3. backend/app/core/settings/env_files/.env - This is the largest env file & it is configuring the backend. It contains configuration like the default superusers to create, Postmark template IDs, password reset urls etc.

## Making migrations
Migrations are handled using [alembic](https://alembic.sqlalchemy.org/en/latest/) & all the migration stuff are stored in backend/alembic.
To run migrations
```
alembic upgrade head
```
If you need to create new migrations, check the alembic docs.

## Tests
This project uses pytest(and the mock package from within unittest for mocking some functions during testing).

To run the tests for the backend
```
cd backend
pytest
```
You can also use the test.sh script in `./backend/scripts`.


## Starting the application

After setting up your .env file appropriately
```
docker-compose up --build
```

### Solving No module named 'backend' or 'worker' or 'commonlib' errors
This is a result of your pythonpath not being set & to resolve, simply add the module of interest to your pythonpath.
On Linux systems, this is adding to your ~/.bashrc file.
```
export PYTHONPATH=$PYTHONPATH://home/alex/Projects/identiko/device_agent_management_server/backend
export PYTHONPATH=$PYTHONPATH://home/alex/Projects/identiko/device_agent_management_server/worker
export PYTHONPATH=$PYTHONPATH://home/alex/Projects/identiko/device_agent_management_server/commonlib
```
Similar things should exist for windows.

black = "*"

### Deploying on a Linux VM
1. Install docker & docker-compose
2. Clone the repo, ensuring you clone the submodules alongside
3. Create the .env files (as explained above) on the VM
4. `docker-compose up --build` to build and run the application


docker-compose -f docker-compose-dev.yml up

