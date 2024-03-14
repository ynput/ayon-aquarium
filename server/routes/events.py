from typing import TYPE_CHECKING
from nxtools import logging

from ayon_server.lib.postgres import Postgres
from ayon_server.entities import UserEntity
from ayon_server.exceptions import NotFoundException

from .sync import syncTopic

if TYPE_CHECKING:
    from .. import AquariumAddon

async def get_event(addon: "AquariumAddon", user: "UserEntity", event_id: str) -> dict:
    """
        Get event by its id and the status of the event it depends on
        When websocket will be available from frontend, this function will be removed
    """
    query = """
        SELECT
        e1.id AS id,
        e1.project_name AS project_name,
        e1.summary AS summary,
        e2.status AS status
        FROM events e1
        LEFT JOIN events e2 ON e2.depends_on = e1.id
        WHERE e1.id = $1 AND e1.topic = $2
    """
    logging.debug(f"Fetching event {event_id}")

    res = await Postgres.fetch(query, event_id, syncTopic)
    if res is None or len(res) == 0:
        raise NotFoundException("Event not found")

    event = res[0]
    print(event)

    if not event:
        raise NotFoundException("Event not found")

    return event