FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

WORKDIR /app/

# Install Poetry
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

RUN pip install --upgrade pip

# Copy poetry.lock* in case it doesn't exist in the repo
COPY ./pyproject.toml ./poetry.lock* /app/

COPY ./prestart.sh /app/


RUN poetry install --no-root --no-dev

COPY . /app

ENV PYTHONPATH=/app
ENV PYTHONPATH "${PYTHONPATH}:/app/commonlib"

ENV MODULE_NAME=backend.app.main
ENV PORT=8000

ENV PRE_START_PATH=/app/backend/prestart.sh
