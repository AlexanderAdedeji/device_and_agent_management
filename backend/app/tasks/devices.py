import time
from typing import Optional
import pika
from pika.adapters.blocking_connection import BlockingChannel
from backend.app.core.settings import settings
from loguru import logger

# parameters = pika.URLParameters(settings.RABBIT_MQ_URI)
# connection = pika.BlockingConnection(parameters=parameters)
# channel = connection.channel()

MAX_SEND_NOTIF_ATTEMPTS = 3


class ConnectionManager:
    def __init__(self) -> None:
        self._connection = None
        self._channel: Optional[BlockingChannel] = None
        self.default_sleep_duration = 5
        self.sleep_duration = self.default_sleep_duration
        self.initialize_connection()

    @property
    def channel(self):
        if not self._channel or self._channel.is_closed or self._connection.is_closed:
            self.initialize_connection()
        return self._channel

    def sleep(self):
        logger.info(f"sleeping for {self.sleep_duration} seconds")
        time.sleep(self.sleep_duration)
        self.sleep_duration *= 2

    def initialize_connection(self):
        logger.info("attempting to initialize rabbit mq connection")
        retries = 0
        MAX_RETRIES = 5
        while retries < MAX_RETRIES:
            retries += 1
            try:
                parameters = pika.URLParameters(settings.RABBIT_MQ_URI)
                parameters.heartbeat = 3600
                connection = pika.BlockingConnection(parameters=parameters)
                channel = connection.channel()
                channel.exchange_declare(
                    exchange="device_updates", exchange_type="direct"
                )
                channel.confirm_delivery()
                self._channel = channel
                self._connection = connection
                logger.info("Connected to Rabbit MQ succesfully [*]")
                self.sleep_duration = self.default_sleep_duration
                return
            except Exception as e:
                logger.error(e)
                logger.info("failed to connect to rabbit mq")
                self.sleep()


connection_manager = ConnectionManager()


def send_notification_to_devices(
    mac_id: str, notification_body: str, attempts_left: int = MAX_SEND_NOTIF_ATTEMPTS
):
    if attempts_left < 0:
        logger.info(f"Failed to deliver to {mac_id}")
        return

    if settings.DEBUG:
        logger.info(f"Mock Sent update to device {mac_id}")
    else:
        try:
            channel = connection_manager.channel
            if not channel:
                logger.error(
                    f"Unable to use rabbit mq to push update to device {mac_id}"
                )
            else:
                channel.basic_publish(
                    exchange="device_updates",
                    routing_key=mac_id,
                    body=notification_body,
                )
        except Exception as e:
            logger.info(e)
            send_notification_to_devices(
                mac_id, notification_body, attempts_left=attempts_left - 1
            )
