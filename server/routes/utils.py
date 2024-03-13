from typing import TYPE_CHECKING, List, Dict

import unicodedata
import contextlib
from typing import Any

from nxtools import slugify

from ayon_server.exceptions import ConflictException
from ayon_server.entities import (FolderEntity, TaskEntity, UserEntity)
from ayon_server.events import dispatch_event
from ayon_server.lib.postgres import Postgres
from ayon_server.settings.anatomy import Anatomy
from ayon_server.settings.anatomy.statuses import Status
from ayon_server.settings.anatomy.task_types import TaskType

if TYPE_CHECKING:
    from .. import AquariumAddon

# GENERAL UTILS
def remove_accents(input_str: str) -> str:
    """Remove accents from a string"""
    nfkd_form = unicodedata.normalize("NFKD", input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def create_short_name(name: str) -> str:
    """Create a short name from a string by removing vowels abbreviating string"""
    code = name.lower()

    if "_" in code:
        subwords = code.split("_")
        code = "".join([subword[0] for subword in subwords])[:4]
    elif len(name) > 4:
        vowels = ["a", "e", "i", "o", "u"]
        filtered_word = "".join([char for char in code if char not in vowels])
        code = filtered_word[:4]

    # if there is a number at the end of the code, add it to the code
    last_char = code[-1]
    if last_char.isdigit():
        code += last_char

    return code


def create_name_and_label(aquarium_name: str) -> dict[str, str]:
    """From a name coming from aquarium, create a name and label"""
    name_slug = slugify(aquarium_name, separator="_")
    return {"name": name_slug, "label": aquarium_name}

# DATABASE UTILS
async def ensure_ayon_project_not_exists(project_name: str, project_code: str):
    async for res in Postgres.iterate(
        "SELECT name FROM projects WHERE name = $1 OR code = $2",
        project_name,
        project_code,
    ):
        raise ConflictException(f"Project {project_name} already exists")
    return None


async def get_user_by_aquarium_key(aquarium_key: str,) -> UserEntity | None:
    """Get an Ayon UserEndtity by its Aquarium _key"""
    res = await Postgres.fetch(
        "SELECT name FROM public.users WHERE data->>'aquariumKey' = $1",
        aquarium_key,
    )
    if not res:
        return None
    user = await UserEntity.load(res[0]["name"])
    return user


async def get_folder_by_aquarium_key(project_name: str, aquarium_key: str, existing_folders: dict[str, str] | None = None) -> FolderEntity | None:
    """Get an Ayon FolderEndtity by its Aquarium _key"""

    if existing_folders and (aquarium_key in existing_folders):
        folder_id = existing_folders[aquarium_key]

    else:
        res = await Postgres.fetch(
            f"""
            SELECT id FROM project_{project_name}.folders
            WHERE data->>'aquariumKey' = $1
            """,
            aquarium_key,
        )
        if not res:
            return None
        folder_id = res[0]["id"]

    return await FolderEntity.load(project_name, folder_id)


async def get_task_by_aquarium_key(project_name: str, aquarium_key: str, existing_tasks: dict[str, str] | None = None) -> TaskEntity | None:
    """Get an Ayon TaskEntity by its Aquarium _key"""

    if existing_tasks and (aquarium_key in existing_tasks):
        folder_id = existing_tasks[aquarium_key]

    else:
        res = await Postgres.fetch(
            f"""
            SELECT id FROM project_{project_name}.tasks
            WHERE data->>'aquariumKey' = $1
            """,
            aquarium_key,
        )
        if not res:
            return None
        folder_id = res[0]["id"]

    return await TaskEntity.load(project_name, folder_id)


# ANATOMY UTILS
async def get_primary_anatomy_preset() -> Anatomy:
    """Get the primary anatomy preset"""

    query = "SELECT * FROM anatomy_presets WHERE is_primary is TRUE"
    async for row in Postgres.iterate(query):
        return Anatomy(**row["data"])
    return Anatomy()

async def parse_task_types(addon: "AquariumAddon", templateTasks: List[Dict[str, Any]]) -> list[TaskType]:
    """
    Map Aquarium template's tasks to Ayon task types
    Aquarium structure:

    {
        "name": "design",
        "startdate": "2024-03-03T23:00:03.372Z",
        "valid": false,
        "status": "TO DO",
        "checklist": [],
        "color": "#FACA12",
        "duration": "P1D",
        "deadline": "2024-03-20T23:00:05.155Z"
    }

    Ayon structure:

    {
        name:
        shortName:
        icon:
    }

    """

    result: list[TaskType] = []
    for aqTask in templateTasks:
        if any(ayonTask.name == aqTask["name"] for ayonTask in result):
            continue

        short_name = ''
        icon = ''

        settings = await addon.get_aquarium_settings()
        found = False
        for task in settings.sync.default.tasks:
            if task.name.lower() == aqTask["name"].lower():
                found = True
                short_name = task.short_name
                icon = task.icon

        if not found:
            short_name = aqTask.get("shortName")
            if not short_name:
                name_slug = remove_accents(aqTask["name"].lower())
                short_name = create_short_name(name_slug)
            icon = "task_alt"

        result.append(
            TaskType(
                original_name=aqTask["name"],
                name=aqTask["name"],
                shortName=short_name,
                icon=icon,
            )
        )

    return result


async def parse_statuses(addon: "AquariumAddon", properties: List[Dict[str, Any]] | None = None) -> list[Status]:
    """
    Map Aquarium status to Ayon status
    Aquarium structure:

    {
        "status": "TO DO",
        "color": "#FBEB06",
        "valid": false,
        "completion": 0
    }

    Ayon structure:

    {
        name,
        shortName,
        state: Literal["not_started", "in_progress", "done", "blocked"],
        icon,
        color,
    }

    """
    result = []
    aqStatuses = []
    if properties == None or len(properties) == 0:
        aqStatuses = addon.aq_default_statuses
    else:
        for propertyData in properties:
            if "tasks_status" in propertyData:
                for taskStatus in propertyData["tasks_status"]:
                    exist = [status for status in aqStatuses if status['status'] == taskStatus['status']]
                    if len(exist) == 0:
                        aqStatuses.append(taskStatus)

    settings = await addon.get_aquarium_settings()

    for aqStatus in aqStatuses:
        name = str(aqStatus["status"])
        shortName = name.lower()
        state = 'not_started'
        icon = 'task_alt'
        color = ''

        found = False
        for (settings_status) in settings.sync.default.status:
            if aqStatus["shortName"] == settings_status.short_name:
                found = True
                icon = settings_status.icon
                state = settings_status.state

        if not found:
            completion = aqStatus.get("completion", None)
            if completion is not None:
                completion = float(completion)
                if completion < 0:
                    state = "blocked"
                elif completion == 0:
                    state = "not_started"
                elif completion < 1:
                    state = "in_progress"
                else:
                    state = "done"

        result.append(Status(
            original_name=name,
            name=name,
            shortName=shortName,
            state=state,
            icon=icon,
            color=color,
        ))

    return result


def parse_attrib(projectData: dict[str, Any], properties: List[Dict[str, Any]] | None = None) -> dict[str, Any]:
    """
    Parse Aquarium project's data and properties to Ayon project's attributes
    """

    result = {}
    if properties is None:
        return result

    if "description" in projectData:
        result["description"] = projectData["description"]

    if "startdate" in projectData:
        result["startDate"] = projectData["startdate"]

    if "deadline" in projectData:
        result["endDate"] = projectData["deadline"]

    for propertyData in properties:
        for key, value in propertyData.items():
            if key == "fps" and value:
                with contextlib.suppress(ValueError):
                    result["fps"] = float(value)
            elif key == "frameStart" and value:
                with contextlib.suppress(ValueError):
                    result["frameStart"] = int(value)
            elif key == "frameEnd" and value:
                with contextlib.suppress(ValueError):
                    result["frameEnd"] = int(value)
            elif key == "resolution" and value:
                try:
                    result["resolutionWidth"] = int(value.split("x")[0])
                    result["resolutionHeight"] = int(value.split("x")[1])
                except (IndexError, ValueError):
                    pass

    return result