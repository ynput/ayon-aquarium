
from typing import TYPE_CHECKING

import time
from ayon_server.helpers.deploy_project import create_project_from_anatomy
from ayon_server.lib.postgres import Postgres

from ayon_server.entities import UserEntity, ProjectEntity
from ayon_server.types import PROJECT_CODE_REGEX, PROJECT_NAME_REGEX, Field, OPModel
from ayon_server.exceptions import AyonException, BadRequestException
from ayon_server.events import dispatch_event

from .anatomy import get_aquarium_project_anatomy
from .sync import trigger_sync_project, SyncProjectRequest
from .utils import ensure_ayon_project_not_exists, create_short_name, set_aquariumKey_on_project

if TYPE_CHECKING:
    from .. import AquariumAddon

class ProjectPaired(OPModel):
    aquariumProjectKey: str | None = Field(..., title="Aquarium project _key")
    aquariumProjectName: str | None = Field(..., title="Aquarium project name")
    aquariumProjectCode: str | None = Field(..., title="Aquarium project code")
    ayonProjectName: str | None = Field(..., title="Ayon project name")

async def get_paired_projects(addon: "AquariumAddon") -> list[ProjectPaired]:
    """
        Get all the projects paired between Aquarium and Ayon.
    """
    ayon_projects: list[dict] = []
    paired_projects: list[ProjectPaired] = []


    async for res in Postgres.iterate(
        """
        SELECT
            name,
            data->>'aquariumProjectKey' AS aquariumProjectKey
        FROM projects
        WHERE active != false
        """
    ):
        ayon_projects.append({"name": res["name"], "aquariumProjectKey": res.get("aquariumprojectkey", None)})

    aqProjects = addon.aq.project.get_all()
    for project in aqProjects:
        aquariumProjectKey: str = project._key
        paired_projects.append(
            ProjectPaired(
                aquariumProjectKey=project._key,
                aquariumProjectName=project.data.name,
                aquariumProjectCode=project.data.code or create_short_name(project.data.name),
                ayonProjectName= next((project["name"] for project in ayon_projects if project['aquariumProjectKey'] == aquariumProjectKey), None)
            )
        )

    for ayonProject in ayon_projects:
        ayonProjectName = ayonProject["name"]
        if ayonProjectName not in [p.ayonProjectName for p in paired_projects]:
            paired_projects.append(
                ProjectPaired(
                    aquariumProjectKey=None,
                    aquariumProjectName=None,
                    aquariumProjectCode=None,
                    ayonProjectName=ayonProjectName,
                )
            )

    return paired_projects

class ProjectsPairRequest(OPModel):
    aquariumProjectKey: str = Field(..., title="Aquarium project _key")
    ayonProjectName: str = Field(
        "...",
        title="Ayon project name",
        regex=PROJECT_NAME_REGEX,
    )

class AlreadyPairedException(AyonException):
    """Raised when a user try to pair a project with Aquarium and it's already paired."""

    detail: str = "Forbidden"
    status: int = 403

async def pair_ayon_project(addon: "AquariumAddon", user: "UserEntity", request: ProjectsPairRequest) -> str:
    """
        Pair an Aquarium project with an existing Ayon project and trigger a full sync.
    """
    project = await ProjectEntity.load(request.ayonProjectName)
    if project.data.get("aquariumProjectKey", None) is not None:
        raise AlreadyPairedException(f"Project {request.ayonProjectName} is already paired with an Aquarium project. Unpair the project first.")

    await set_aquariumKey_on_project(request.ayonProjectName, request.aquariumProjectKey)
    addon.aq.project(request.aquariumProjectKey).update_data(data={"ayonProjectName": request.ayonProjectName})

    return await trigger_sync_project(
        addon,
        project_name=request.ayonProjectName,
        user=user,
        aquarium_project_key=request.aquariumProjectKey,
    )

class ProjectsCreateRequest(OPModel):
    aquariumProjectKey: str | None = Field(None, title="Aquarium project _key")
    aquariumProjectName: str | None = Field(None, title="Aquarium project name")
    ayonProjectName: str = Field(
        "...",
        title="Ayon project name",
        regex=PROJECT_NAME_REGEX,
    )
    ayonProjectCode: str = Field(
        "...",
        title="Ayon project code",
        regex=PROJECT_CODE_REGEX,
    )

async def create_ayon_project(addon: "AquariumAddon", user: "UserEntity", request: ProjectsCreateRequest):
    """
        Create an Aquarium project on Ayon project and trigger a full sync.
    """
    if request.aquariumProjectKey is None:
        raise BadRequestException("aquariumProjectKey should be provided when creating a Ayon project.")

    await ensure_ayon_project_not_exists(
        request.ayonProjectName,
        request.ayonProjectCode,
    )

    anatomy = await get_aquarium_project_anatomy(addon, request.ayonProjectName, request.aquariumProjectKey)

    try:
        await create_project_from_anatomy(
            name=request.ayonProjectName,
            code=request.ayonProjectCode,
            anatomy=anatomy,
            library=False,
        )
    except Exception as e:
        raise Exception(f"Failed to create project: {e}")

    await set_aquariumKey_on_project(request.ayonProjectName, request.aquariumProjectKey)
    addon.aq.project(request.aquariumProjectKey).update_data(data={"ayonProjectName": request.ayonProjectName})

    return await trigger_sync_project(
        addon,
        project_name=request.ayonProjectName,
        user=user,
        aquarium_project_key=request.aquariumProjectKey,
    )

async def create_aquarium_project(addon: "AquariumAddon", user: "UserEntity", request: ProjectsCreateRequest):
    """
        Create an Ayon project on Aquarium and trigger a full sync.
    """
    project = await ProjectEntity.load(request.ayonProjectName)
    if project.data.get("aquariumProjectKey", None) is not None:
        raise AlreadyPairedException(f"Project {request.ayonProjectName} is already paired with an Aquarium project. Unpair the project first.")

    eventId = await dispatch_event(
        'aquarium.project_create',
        hash=f"create_aquarium_project_{request.ayonProjectName}_{time.time()}",
        description="Create Ayon's project to Aquarium",
        project=request.ayonProjectName,
        user=user.name,
        payload={
            "aquariumProjectName": request.aquariumProjectName or request.ayonProjectName,
        })

    return eventId



async def unpair_project(addon: "AquariumAddon", user: "UserEntity", project_name: str):
    """
        Unpair an Aquarium project.
    """
    project = await ProjectEntity.load(project_name)
    aquariumProjectKey = project.data['aquariumProjectKey']

    addon.aq.project(aquariumProjectKey).update_data(data={"ayonProjectName": None})

    project.data['aquariumProjectKey'] = None
    await project.save()
