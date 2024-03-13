import sys
import time
import signal
import logging
import threading
import traceback
from typing import Any, Union

from aquarium import Aquarium
from aquarium import exceptions

from aquarium_common import AquariumServices, connect_to_ayon, register_signals

import ayon_api

IGNORE_TOPICS = {}

log = logging.getLogger(__name__)
_AQS = AquariumServices()


def create_event_description(event):
    return "Received {topic} #{_key}".format(topic=event.topic, _key=event._key)


def callback(event):
    if event.topic in IGNORE_TOPICS:
        return

    ayon_api.dispatch_event(
        "aquarium.leech",
        sender=ayon_api.ServiceContext.service_name,
        event_hash=event._key,
        description="Received {topic} #{_key}".format(topic=event.topic, _key=event._key),
        payload=event.to_dict(),
    )

    log.info(f"Event stored {event.topic}")


def main():
    logging.basicConfig(level=logging.INFO)

    connect_to_ayon()
    register_signals(_AQS)

    while not _AQS.connected:
        _AQS.connect()
        if _AQS.connected is False:
            time.sleep(10)
            continue

        _AQS.session_fail_logged = False
        _AQS.listen()

        if _AQS.listener is not None:
            _AQS.listener.subscribe("*", callback)
            _AQS.listener.start()
