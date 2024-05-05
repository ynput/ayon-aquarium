import sys
import time
import signal
import logging
import threading
import traceback
from typing import Any, Optional, Union

from aquarium import Aquarium
from aquarium import exceptions

from aquarium_common import (
    AquariumServices,
    connect_to_ayon,
    register_signals,
    IGNORED_AQ_TOPICS,
    ALLOWED_AQ_TOPICS,
)

import ayon_api


log = logging.getLogger(__name__)
_AQS = AquariumServices()


def create_event_description(event):
    return "Received {topic} #{_key}".format(topic=event.topic, _key=event._key)


def create_event_topic(event) -> Optional[str]:
    """Returns AYON event topic from Aquarium event topic.
    Aquarium Examples:
        user.assigned
        item.created.Task
    Output Examples:
        aq.leech.user.assigned
        aq.leech.task.created
    """
    parts = event.topic.split(".")
    parts = [p.lower() for p in parts]
    log.debug(f"{parts = }")
    supported_items = {
        "asset",
        "shot",
        "sequence",
        "episode",
        "task",
        "user",
        "project",
    }
    cmd, item = None, None
    for _item in supported_items:
        if _item in parts:
            item = _item
            cmd = parts[1]  #! might not be supported by processor
            break

    if not all([cmd, item]):
        return None

    result = ["aq", "leech", item, cmd]
    result = ".".join(result)
    log.debug(f"Event topic created {result}")
    return result


def callback(event):
    """Callback function for Aquarium event listener."""
    if event.topic in IGNORED_AQ_TOPICS:
        log.warning(f"Event topic ignored: {event.topic}")
        return

    if event.topic not in ALLOWED_AQ_TOPICS:
        log.warning(f"Event topic not allowed: {event.topic}")
        return

    ay_topic = create_event_topic(event)
    if not ay_topic:
        log.warning(f"Can't build ayon topic for: {event.topic}")
        return

    if ayon_api.dispatch_event(
        ay_topic,
        sender=ayon_api.ServiceContext.service_name,
        event_hash=event._key,
        description=create_event_description(event),
        payload=event.to_dict(),
    ):
        log.info(f"Created event {ay_topic}")
    log.warning(f"Failed to create event {ay_topic}")


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
