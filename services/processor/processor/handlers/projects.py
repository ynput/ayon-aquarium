from typing import TYPE_CHECKING

import ayon_api
import logging

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

def sync(processor: "AquariumProcessor", aquariumProjectKey: str):
    log.info(f"Full sync project #{aquariumProjectKey}")
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
            "path": "REVERSE(APPEND(mainPath, SHIFT(path.vertices)))" # REVERSE to match event path order and SHIFT to avoid item deduplication
        },
        "view": {
            "type": "type",
            "items": "items"
        }
    }
    collections: list = processor._AQS.aq.project(aquariumProjectKey).traverse(meshql=query, aliases=aliases)

    items = {}
    cast = processor._AQS.aq.cast
    for itemType in collections:
        items[itemType["type"]] = []
        for item in itemType["items"]:
            items[itemType["type"]].append({
                "folder": ayonise_folder(cast(item['folder'])),
                "tasks": [dict(task=ayonise_task(cast(task["task"])), path=task["path"]) for task in item['tasks']],
                "path": item['path']
            })

    ayon_api.post(
        f"{processor.entrypoint}/projects/{project_name}/sync/all",
        items=items
    )

