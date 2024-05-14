import time
import logging
from typing import List, Set


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


def callback(event):
    """Callback function for Aquarium event listener.
    Checks the event data for item, gets corresponding project, then dispatches an event to Ayon.
    """

    # get aq item from event
    event_data = event.to_dict()
    item = event_data["data"].get("item")
    item_key = item.get("_id")
    if not all([item, item_key]):
        log.error(f"Can't retrieve Aquarium item from event: {event_data}")
        return
    aq_item = _AQS.aq.cast(item)

    # get project from item
    query = "# <($Child, 5)- item.type == 'Project'"
    projects: List[dict] = aq_item.traverse(meshql=query)
    if len(projects) > 1:
        log.error(f"More than one project found for item: {item_key}")
        return
    if len(projects) == 0:
        log.error(f"No project found for item: {item_key}")
        return
    aq_project = _AQS.aq.cast(projects[0].get("item"))
    aq_project = aq_project.to_dict()  # convert to dict for easier access

    # check if project is in Ayon
    if not aq_project.get("data").get("ayonProjectName"):
        log.warning(
            f"Project {aq_project['data']['name']} is not set up to track with Ayon"
        )
        return

    ay_project = ayon_api.get_project(aq_project["data"]["ayonProjectName"])

    if ayon_api.dispatch_event(
        "aquarium.leech",
        project_name=ay_project["name"],  # why u no work?
        sender=ayon_api.ServiceContext.service_name,
        event_hash=event._key,
        description=create_event_description(event),
        payload=event.to_dict(),
    ):
        log.info(f"Created event for topic: {event.topic}")
    else:
        log.warning(f"Failed to create event for topic: {event.topic}")


def main():
    logging.basicConfig(level=logging.INFO)

    connect_to_ayon()
    register_signals(_AQS)

    supported_events: Set = ALLOWED_AQ_TOPICS - IGNORED_AQ_TOPICS
    while not _AQS.connected:
        _AQS.connect()
        if _AQS.connected is False:
            time.sleep(10)
            continue

        _AQS.session_fail_logged = False
        _AQS.listen()

        if _AQS.listener is not None:
            for event in supported_events:
                log.info(f"Subscribing to {event}")
                _AQS.listener.subscribe(event, callback)
            _AQS.listener.start()
