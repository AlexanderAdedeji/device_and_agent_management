#!/usr/bin/env bash

alembic upgrade head

uvicorn app.main:app --reload