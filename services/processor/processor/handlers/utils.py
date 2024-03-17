""" utils shared between fullsync.py and update_from_aquarium.py """
from typing import TYPE_CHECKING
import unicodedata
import logging
from nxtools import slugify

import ayon_api

if TYPE_CHECKING:
    from ..processor import AquariumProcessor

log = logging.getLogger(__name__)
ayonUsers = None  # Declare ayonUsers as a global variable

def unaccent(input_str: str) -> str:
    """Remove accents from a string"""
    nfkd_form = unicodedata.normalize("NFKD", input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])


def get_ayon_users():
    """Create a map of Ayon users name by their email address."""
    global ayonUsers  # Use the global variable ayonUsers

    if ayonUsers is None:
        ayonUsers = {
            user["attrib"]["email"]: user["name"] for user in ayon_api.get_users()
        }

    return ayonUsers

def ayonise_folder(aqItem) -> dict[str, str]:
    """Convert an Aquarium item to an Ayon folder entity structure."""
    ayonised = {
        "name": slugify(aqItem.data.name, separator="_"),
        "label": aqItem.data.name,
        "folderType": aqItem.type,
        "data": {
            "aquariumKey": aqItem._key
        },
        "attrib": {}
    }

    if aqItem.data.ayonId:
        ayonised['id'] = aqItem.data.ayonId

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

def ayonise_task(aqTask, aqUserEmails) -> dict[str, str]:
    """Convert an Aquarium task to an Ayon task entity structure."""

    ayonised = {
        "name": slugify(aqTask.data.name, separator="_"),
        "label": aqTask.data.name,
        "data": {
            "aquariumKey": aqTask._key
        },
        "attrib": {},
        "assignees": []
    }

    if aqTask.data.ayonId:
        ayonised['id'] = aqTask.data.ayonId

    if 'status' in aqTask.data:
        ayonised['status'] = aqTask.data.status

    if 'tags' in aqTask.data:
        ayonised['tags'] = aqTask.data.tags

    if 'description' in aqTask.data:
        ayonised['attrib']['description'] = aqTask.data.description

    ayon_users = get_ayon_users()
    for aqUserEmail in aqUserEmails:
        if aqUserEmail in ayon_users:
            ayonised['assignees'].append(ayon_users[aqUserEmail])

    return ayonised