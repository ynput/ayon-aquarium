from typing import TYPE_CHECKING

import ayon_api
import logging
from functools import reduce

from .utils import ayonise_folder, ayonise_task

if TYPE_CHECKING:
    from ..processor import AquariumProcessor

log = logging.getLogger(__name__)

def updated(processor: "AquariumProcessor", event):
    log.info(f"Update projet {event.data.item.data.name}")
    projectKey = event.data.item._key
    project_name = processor.get_paired_ayon_project(projectKey)
    if not project_name:
        return  # do nothing as aquarium and ayon project are not paired

    attributes = ayon_api.get(
        f"{processor.entrypoint}/projects/{project_name}/anatomy/attributes"
    )

    payload = {
        "attrib": attributes.data,
    }

    ayon_api.patch(
        f"/projects/{project_name}",
        json=payload
    )

def sync(processor: "AquariumProcessor", aquariumProjectKey: str, eventId: str):
    log.info(f"Gathering data for sync project #{aquariumProjectKey}...")
    project_name = processor.get_paired_ayon_project(aquariumProjectKey)
    if not project_name:
        return  # do nothing as aquarium and ayon project are not paired

    query = "# -($Child, 3)> 0,1000 item.type IN ['Episode', 'Sequence', 'Shot', 'Library', 'Asset'] SET $set COLLECT type = item.type INTO items = $items SORT null VIEW $view"
    aliases = {
        "set": {
            "mainPath": "path.vertices",
        },
        "items": {
            "folder": "item",
            "tasks": "# -($Child)> $Task SORT null VIEW $taskView",
            "path": "REVERSE(mainPath)" # REVERSE the path to match event path order
        },
        "taskView": {
            "task": "item",
            "assignees": "# -($Assigned)> $User SORT null VIEW item.data.email",
            "path": "REVERSE(APPEND(mainPath, SHIFT(path.vertices)))" # REVERSE to match event path order and SHIFT to avoid item deduplication
        },
        "view": {
            "type": "type",
            "items": "items"
        }
    }
    collections: list = processor._AQS.aq.project(aquariumProjectKey).traverse(meshql=query, aliases=aliases)
    log.info(f"{len(collections)} items type found for project #{aquariumProjectKey}.")

    items = {}
    eventSummary = {}
    cast = processor._AQS.aq.cast
    for itemType in collections:
        log.debug(f"Processing {itemType['type']} items...")
        items[itemType["type"]] = []
        for item in itemType["items"]:
            log.debug(f"  - Processing {item['folder']['data']['name']}...")
            items[itemType["type"]].append({
                "folder": ayonise_folder(cast(item['folder'])),
                "tasks": [dict(task=ayonise_task(cast(task["task"]), task['assignees']), path=task["path"]) for task in item['tasks']],
                "path": item['path']
            })

            # items[itemType["type"]] = [{folder, tasks: []}]
        eventSummary[itemType["type"]] = {
            "count": reduce(lambda count, item: count + 1 + len(item["tasks"]), items[itemType["type"]], 0),
            "error": None,
            "progression": 0
        }

    ayon_api.update_event(
        eventId,
        sender=ayon_api.get_service_addon_name(),
        summary=eventSummary
    )

    res = ayon_api.post(
        f"{processor.entrypoint}/projects/{project_name}/sync/all",
        items=items,
        eventId=eventId
    )

    try:
        res.raise_for_status()
        log.info(f"Sync data processed and submitted for project #{aquariumProjectKey}.")
    except Exception as e:
        log.error(f"Error while syncing project {aquariumProjectKey} to Ayon: {e}")
        return

