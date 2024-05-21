from .utils import ayonise_task

import ayon_api
import logging
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..processor import AquariumProcessor

log = logging.getLogger(__name__)

def created(processor: "AquariumProcessor", event):
    sync_task(processor, event)

def updated(processor: "AquariumProcessor", event):
    sync_task(processor, event)

def assigned(processor: "AquariumProcessor", event):
    sync_task(processor, event)

def sync_task(processor: "AquariumProcessor", event):
    """Send sync request to Aquarium addon API."""
    context = event.get_context()
    aqTask = context["path"][0]
    aqProject = context["project"]

    project_name = processor.get_paired_ayon_project(aqProject._key)
    if not project_name:
        return  # do nothing as aquarium and ayon project are not paired

    aqUserEmails = aqTask.traverse(meshql="# -($Assigned)> $User VIEW item.data.email")
    task = ayonise_task(aqTask, aqUserEmails)

    response = ayon_api.post(
        f"{processor.entrypoint}/projects/{project_name}/sync/task",
        task=task,
        path=[item.to_dict() for item in context["path"]],
    )

    try:
        response.raise_for_status()
    except Exception as e:
        log.error(f"Error while syncing {aqTask.type} {aqTask._key}: {e}")
