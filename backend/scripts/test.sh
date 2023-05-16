#!/usr/bin/env bash

alembic upgrade head

coverage run -m pytest 

coverage report