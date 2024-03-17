from typing import Type

from nxtools import logging

from ayon_server.addons import BaseServerAddon
from ayon_server.api.dependencies import CurrentUser, ProjectName
from ayon_server.api.responses import EmptyResponse

from ayon_server.exceptions import InvalidSettingsException, ForbiddenException
from ayon_server.secrets import Secrets

from .settings import AquariumSettings

from .routes.pairing import (
    get_paired_projects, ProjectPaired,
    pair_ayon_project, ProjectsPairRequest,
    create_ayon_project, create_aquarium_project, ProjectsCreateRequest,
    unpair_project)

from .routes.sync import (
    trigger_sync_project,
    sync_project, SyncProjectRequest,
    sync_folder, SyncFolderRequest,
    sync_task, SyncTaskRequest)

from .routes.anatomy import (
    get_aquarium_project_anatomy, ProjectAttribModel
)

from .routes.events import get_event


from .vendors.aquarium import Aquarium, DEFAULT_STATUSES

try:
    from .version import __version__ # type: ignore
except ModuleNotFoundError:
    # temporary solution for local development
    # version is pushed from package.py in ayon >= 1.0.3
    __version__ = "0.0.0"

class AquariumAddon(BaseServerAddon):
    """
    Aquarium server addon for Ayon
    Responsible for:
        - Adding API endpoint for pairing, syncing and getting project anatomy

    FIXME: Build dependency, to remove vendors folder
    """
    name = "aquarium"
    title = "Aquarium"
    version = __version__
    settings_model: Type[AquariumSettings] = AquariumSettings
    frontend_scopes = {
        "settings": {},
    }
    services = {
        "leecher": {"image": f"ynput/ayon-aquarium-leecher:{__version__}"},
        "processor": {"image": f"ynput/ayon-aquarium-processor:{__version__}"}
    }

    bot_key: str
    aq: Aquarium = Aquarium()
    aq_default_statuses = list(DEFAULT_STATUSES.values())

    frontend_scopes: dict[str, dict[str, str]] = {"project": {"sidebar": "hierarchy"}}

    def initialize(self):
        logging.info("Initializing Aquarium addon...")

        self.add_endpoint("/projects/pair", self.GET_projects_paired, method="GET")
        self.add_endpoint("/projects/pair", self.POST_projects_pair, method="POST")
        self.add_endpoint("/projects", self.POST_projects_create, method="POST")
        self.add_endpoint("/projects/{project_name}/pair", self.DELETE_projects_pair, method="DELETE")
        self.add_endpoint("/projects/{project_name}/sync", self.POST_projects_sync, method="POST")
        self.add_endpoint("/projects/{project_name}/sync/all", self.POST_projects_sync_all, method="POST")
        self.add_endpoint("/projects/{project_name}/sync/folder", self.POST_projects_sync_folder, method="POST")
        self.add_endpoint("/projects/{project_name}/sync/task", self.POST_projects_sync_task, method="POST")
        self.add_endpoint("/projects/{project_name}/anatomy/attributes", self.GET_anatomy_attributes, method="GET")
        self.add_endpoint("/events/{event_id}", self.GET_event, method="GET")

        logging.info("Aquarium addon initialized.")

    """
    Aquarium server controllers are defined here to keep fastapi request validation.
    To keep code logic easier to understand, we would like to keep the controllers into the routes folder.
    But we didn't handle it because of the fastapi request validation.
    """

    # GET /projects/pair
    async def GET_projects_paired(self) -> list[ProjectPaired]:
        await self.connect_aquarium()
        return await get_paired_projects(self)

    # POST /projects
    async def POST_projects_create(self, user: CurrentUser, request: ProjectsCreateRequest) -> EmptyResponse:
        if not user.is_manager:
            raise ForbiddenException("Only managers can create projects")

        await self.connect_aquarium()
        if request.aquariumProjectKey is None:
            await create_aquarium_project(self, user, request)
        else:
            await create_ayon_project(self, user, request)
        return EmptyResponse(status_code=201)

    # POST /projects/pair
    async def POST_projects_pair(self, user: CurrentUser, request: ProjectsPairRequest) -> EmptyResponse:
        if not user.is_manager:
            raise ForbiddenException("Only managers can pair projects")

        await self.connect_aquarium()
        await pair_ayon_project(self, user, request)
        return EmptyResponse(status_code=201)

    # DELETE /projects/pair
    async def DELETE_projects_pair(self, user: CurrentUser, project_name: ProjectName) -> EmptyResponse:
        if not user.is_manager:
            raise ForbiddenException("Only managers can unpair Aquarium projects")

        await self.connect_aquarium()
        await unpair_project(self, user, project_name)
        return EmptyResponse(status_code=201)

    # POST /projects/{project_name}/sync
    async def POST_projects_sync(self, user: CurrentUser, project_name: ProjectName) -> str:
        if not user.is_manager:
            raise ForbiddenException("Only managers can sync Aquarium projects")

        return await trigger_sync_project(self, project_name, user)

    # POST /projects/{project_name}/sync/all
    async def POST_projects_sync_all(self, user: CurrentUser, project_name: ProjectName, request: SyncProjectRequest) -> str:
        return await sync_project(self, project_name, user, request)

    # POST /projects/{project_name}/sync/folder
    async def POST_projects_sync_folder(self, user: CurrentUser, project_name: ProjectName, request: SyncFolderRequest) -> str:
        return await sync_folder(self, project_name, user, request)

    # POST /projects/{project_name}/sync/task
    async def POST_projects_sync_task(self, user: CurrentUser, project_name: ProjectName, request: SyncTaskRequest) -> str:
        return await sync_task(self, project_name, user, request)

    # GET /projects/{project_name}/anatomy/attributes
    async def GET_anatomy_attributes(self, project_name: ProjectName) -> ProjectAttribModel:
        await self.connect_aquarium()
        anatomy = await get_aquarium_project_anatomy(self, project_name)
        return anatomy.attributes

    # GET /events/{event_id}
    async def GET_event(self, user: CurrentUser, event_id: str) -> dict:
        if not user.is_manager:
            raise ForbiddenException("Only managers can get event details")

        return await get_event(self, user, event_id)


    async def setup(self):
        pass

        # If the addon makes a change in server configuration,
        # e.g. adding a new attribute, you may trigger a server
        # restart by calling self.restart_server()
        # Use it with caution and only when necessary!
        # You don't want to restart the server every time the addon is loaded.

        # self.request_server_restart()

    #
    # Helpers
    #
    async def get_aquarium_settings(self) -> AquariumSettings:
        """
        Return Aquarium settings from the database.
        Function created to improve typing.
        """
        return await self.get_studio_settings() # type: ignore

    async def connect_aquarium(self, mock: bool = False):
        """
        Signin addon to Aquarium server using Ayon settings.
        """

        if self.aq.token is not None and self.aq.token != '':
            return

        if mock is True:
            raise NotImplementedError("Mock is not implemented")
            # self.aquarium = AquariumMock()
            # return

        settings = await self.get_aquarium_settings()
        if not settings.url:
            raise InvalidSettingsException("Aquarium server is not set")

        actual_bot_key = await Secrets.get(settings.services.bot_key)
        actual_bot_secret = await Secrets.get(settings.services.bot_secret)

        if not actual_bot_key:
            raise InvalidSettingsException("Aquarium bot_key secret is not set")

        if not actual_bot_secret:
            raise InvalidSettingsException("Aquarium bot_secret secret is not set")

        self.aq.api_url = settings.url
        self.aq.domain = settings.domain
        self.aq.bot(actual_bot_key).signin(actual_bot_secret)

        self.bot_key = actual_bot_key