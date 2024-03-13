""" utils shared between fullsync.py and update_from_aquarium.py """
from typing import TYPE_CHECKING
import logging

import ayon_api

if TYPE_CHECKING:
    from ..processor import AquariumProcessor

log = logging.getLogger(__name__)

def get_ayon_users():
    """Create a map of Ayon users name by their email address."""
    return {
        user["attrib"]["email"]: user["name"] for user in ayon_api.get_users()
    }

def ayonise_folder(aqItem) -> dict[str, str]:
    """Convert an Aquarium item to an Ayon folder entity structure."""
    ayonised = {
        "name": aqItem.data.name,
        "label": aqItem.data.name,
        "folderType": aqItem.type,
        "data": {
            "aquariumKey": aqItem._key
        },
        "attrib": {}
    }

    if 'status' in aqItem.data:
        ayonised['status'] = aqItem.data.status

    if 'tags' in aqItem.data:
        ayonised['tags'] = aqItem.data.tags

    if 'description' in aqItem.data:
        ayonised['attrib']['description'] = aqItem.data.description

    return ayonised

def sync_folder(processor: "AquariumProcessor", event):
    """Send sync request to Aquarium addon API."""

    context = event.get_context()
    aqItem = context["path"][0]
    # FIXME: Change to context['project'] on next aquarium-python-api release
    aqProject = context["path"][-1]

    project_name = processor.get_paired_ayon_project(aqProject._key)
    if not project_name:
        return  # do nothing as aquarium and ayon project are not paired

    folder = ayonise_folder(aqItem)
    response = ayon_api.post(
        f"{processor.entrypoint}/projects/{project_name}/sync/folder",
        folder=folder,
        path=[item.to_dict() for item in context["path"]],
    )

    try:
        response.raise_for_status()
    except Exception as e:
        log.error(f"Error while syncing {aqItem.type} {aqItem._key}: {e}")

def ayonise_task(aqTask) -> dict[str, str]:
    """Convert an Aquarium task to an Ayon task entity structure."""

    ayonised = {
        "name": aqTask.data.name,
        "label": aqTask.data.name,
        "data": {
            "aquariumKey": aqTask._key
        },
        "attrib": {},
        "assignees": []
    }

    if 'status' in aqTask.data:
        ayonised['status'] = aqTask.data.status

    if 'tags' in aqTask.data:
        ayonised['tags'] = aqTask.data.tags

    if 'description' in aqTask.data:
        ayonised['attrib']['description'] = aqTask.data.description

    ayon_users = get_ayon_users()
    aqUserEmails = aqTask.traverse(meshql="# -($Assigned)> $User VIEW item.data.email")
    for aqUserEmail in aqUserEmails:
        if aqUserEmail in ayon_users:
            ayonised['assignees'].append(ayon_users[aqUserEmail])

    return ayonised

def sync_task(processor: "AquariumProcessor", event):
    """Send sync request to Aquarium addon API."""
    context = event.get_context()
    aqTask = context["path"][0]
    # FIXME: Change to context['project'] on next aquarium-python-api release
    aqProject = context["path"][-1]

    project_name = processor.get_paired_ayon_project(aqProject._key)
    if not project_name:
        return  # do nothing as aquarium and ayon project are not paired

    task = ayonise_task(aqTask)
    response = ayon_api.post(
        f"{processor.entrypoint}/projects/{project_name}/sync/task",
        task=task,
        path=[item.to_dict() for item in context["path"]],
    )

    try:
        response.raise_for_status()
    except Exception as e:
        log.error(f"Error while syncing {aqTask.type} {aqTask._key}: {e}")
