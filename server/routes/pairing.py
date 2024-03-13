
from typing import TYPE_CHECKING

from ayon_server.helpers.deploy_project import create_project_from_anatomy
from ayon_server.lib.postgres import Postgres

from ayon_server.entities import UserEntity
from ayon_server.types import PROJECT_CODE_REGEX, PROJECT_NAME_REGEX, Field, OPModel

from .anatomy import get_aquarium_project_anatomy
from .sync import trigger_sync_project, SyncProjectRequest
from .utils import ensure_ayon_project_not_exists, create_short_name

if TYPE_CHECKING:
    from .. import AquariumAddon

class ProjectPaired(OPModel):
    aquariumProjectKey: str = Field(..., title="Aquarium project _key")
    aquariumProjectName: str = Field(..., title="Aquarium project name")
    aquariumProjectCode: str | None = Field(None, title="Aquarium project code")
    ayonProjectName: str | None = Field(..., title="Ayon project name")

async def get_paired_projects(addon: "AquariumAddon") -> list[ProjectPaired]:
    """
        Get all the projects paired between Aquarium and Ayon.
    """
    ayon_projects: dict[str, str] = {}
    paired_projects: list[ProjectPaired] = []


    async for res in Postgres.iterate(
        """
        SELECT
            name,
            data->>'aquariumProjectKey' AS aquariumProjectKey
        FROM projects
        WHERE data->>'aquariumProjectKey' IS NOT NULL
        """
    ):
        ayon_projects[res["aquariumprojectkey"]] = res["name"]

    aqProjects = addon.aq.project.get_all()
    for project in aqProjects:
        paired_projects.append(
            ProjectPaired(
                aquariumProjectKey=project._key,
                aquariumProjectName=project.data.name,
                aquariumProjectCode=project.data.code or create_short_name(project.data.name),
                ayonProjectName=ayon_projects.get(project._key),
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
    ayonProjectCode: str = Field(
        ...,
        title="Ayon project code",
        regex=PROJECT_CODE_REGEX,
    )

async def pair_project(addon: "AquariumAddon", user: "UserEntity", request: ProjectsPairRequest):
    """
        Pair an Aquarium project with an Ayon project and trigger a full sync.
    """
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

    prj_data = {
        "aquariumProjectKey": request.aquariumProjectKey,
    }

    await Postgres.execute(
        """UPDATE projects SET data=$1 WHERE name=$2""",
        prj_data,
        request.ayonProjectName,
    )

    await trigger_sync_project(
        addon,
        project_name=request.ayonProjectName,
        user=user,
        aquarium_project_key=request.aquariumProjectKey,
    )
