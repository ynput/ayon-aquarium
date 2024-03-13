from typing import TYPE_CHECKING

from ayon_server.entities.project import ProjectEntity
from ayon_server.settings.anatomy import Anatomy, ProjectAttribModel # Keep this import for server controllers
from ayon_server.lib.postgres import Postgres

from .utils import parse_attrib, parse_statuses, parse_task_types, get_primary_anatomy_preset

if TYPE_CHECKING:
    from .. import AquariumAddon

async def get_aquarium_project_anatomy(addon: "AquariumAddon", project_name: str, aquarium_project_key: str | None = None) -> Anatomy:
    """
        Get the anatomy of a project from Aquarium.
        If the aquarium_project_key is not provided, it will be fetched from the database.
    """
    if aquarium_project_key is None:
        async for res in Postgres.iterate(
            "SELECT data->>'aquariumProjectKey' FROM projects WHERE name = $1",
            project_name,
        ):
            aquarium_project_key = res[0]

    projectQuery = "# 0,1 item._key == @projectKey VIEW $view"
    projectAliases = {
        "projectKey": aquarium_project_key,
        "view": {
            "item": "item",
            "properties": "# -($Child)> $Properties VIEW item.data"
        }
    }
    aqProjects = addon.aq.query(meshql=projectQuery, aliases=projectAliases)

    if len(aqProjects) == 0:
        raise Exception("Project not found on Aquarium")

    aqProject = aqProjects[0]
    attributes = parse_attrib(aqProject["item"], aqProject["properties"])
    statuses = await parse_statuses(addon, aqProject["properties"])

    templateTasksQuery = "# -($Child, 3)> $Template AND item.data.templateData.type IN ['Library', 'Asset', 'Episode', 'Sequence', 'Shot'] -($Child, 2)> $Task SORT edge.data.weight ASC VIEW $view"
    templateTasksAliases = {
        "view": {
            "name": "item.data.name",
            "shortName": "item.data.shortName",
            "icon": "item.data.icon",
        }
    }
    aqTemplateTasks = addon.aq.project(aquarium_project_key).traverse(meshql=templateTasksQuery, aliases=templateTasksAliases)
    task_types = await parse_task_types(addon, aqTemplateTasks)

    anatomy_preset = await get_primary_anatomy_preset()
    anatomy_dict = anatomy_preset.dict()

    anatomy_dict["attributes"] = attributes
    anatomy_dict["statuses"] = statuses
    anatomy_dict["task_types"] = task_types

    return Anatomy(**anatomy_dict)

async def get_ayon_project(project_name: str) -> ProjectEntity:
    """
        Get Ayon's project entity.
    """
    projectEntity = await ProjectEntity.load(project_name)
    return projectEntity