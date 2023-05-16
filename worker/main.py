import json
from typing import Any, Callable, Dict

import pika
from loguru import logger
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

from config import (
    RABBIT_MQ_URI,
    RABBIT_MQ_EXCHANGE_TYPE,
    RABBIT_MQ_ROUTING_KEYS,
    RABBIT_MQ_EXCHANGE_NAME,
    DEFAULT_RABBIT_MQ_CONNECTION_RETRY_SECONDS,
)
from db.models.log import Log
from db.repositories.log import log_repository
import time


def connect_to_rabbitmq(message_callback: Callable):
    parameters = pika.URLParameters(RABBIT_MQ_URI)
    parameters.heartbeat = 3600
    connection = pika.BlockingConnection(parameters=parameters)
    channel = connection.channel()

    channel.exchange_declare(
        exchange=RABBIT_MQ_EXCHANGE_NAME, exchange_type=RABBIT_MQ_EXCHANGE_TYPE
    )

    result = channel.queue_declare(queue="", exclusive=True)
    queue_name = result.method.queue

    for ROUTING_KEY in RABBIT_MQ_ROUTING_KEYS:
        channel.queue_bind(
            exchange=RABBIT_MQ_EXCHANGE_NAME, queue=queue_name, routing_key=ROUTING_KEY
        )

    channel.basic_consume(
        queue=queue_name, on_message_callback=message_callback, auto_ack=True
    )

    logger.info(" [*] Listening for logs ...")
    channel.start_consuming()


def message_callback(
    ch: BlockingChannel, method: Basic.Deliver, properties: BasicProperties, body: bytes
):
    logger.info(
        "message -  {} \n received on routing key -  {}".format(
            body, method.routing_key
        )
    )

    try:
        log_data = json.loads(body)
        log_repository.create(obj_in=Log(**log_data))
        logger.info("created log {}".format(log_data))
    except Exception as e:
        logger.error(e)


current_retry_seconds = DEFAULT_RABBIT_MQ_CONNECTION_RETRY_SECONDS / 2
max_retry_seconds = 60
while True:
    current_retry_seconds = min(max_retry_seconds, current_retry_seconds * 2)
    try:
        connect_to_rabbitmq(message_callback)
    except Exception as e:
        logger.error(e)
        logger.info(f"re attempting connection in {current_retry_seconds} seconds")
        time.sleep(current_retry_seconds)
