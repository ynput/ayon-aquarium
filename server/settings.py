
from pydantic import Field

from ayon_server.settings import BaseSettingsModel
from ayon_server.settings.enum import secrets_enum
from ayon_server.settings.anatomy.statuses import State

class AquariumServiceSettings(BaseSettingsModel):
    """
    Aquarium services cares about handling Aquarium event and process them
    before sending them to addon's server API.

    To be able do that work it is required to listen (leecher) and process (processor) events
    as one of aquarium bot.It is recommended to use a dedicated bot for that purposes
    so you can see which changes happened from service.
    """

    bot_key: str = Field(
        '',
        placeholder="Select your bot key from Ayon secrets",
        enum_resolver=secrets_enum,
        title="Bot key",
        description="Enter your Aquarium bot key",
    )
    bot_secret: str = Field(
        '',
        placeholder="Select your bot secret from Ayon secrets",
        enum_resolver=secrets_enum,
        title="Bot secret",
        description="Enter your Aquarium bot secret",
    )

class TaskCondition(BaseSettingsModel):
    _layout: str = "compact"
    name: str = Field("", title="Name")
    short_name: str = Field("", title="Short name")
    icon: str = Field("task_alt", title="Icon", widget="icon")

def _states_enum():
    return [
        {"value": "not_started", "label": "Not started"},
        {"value": "in_progress", "label": "In progress"},
        {"value": "done", "label": "Done"},
        {"value": "blocked", "label": "Blocked"},
    ]

class StatusCondition(BaseSettingsModel):
    _layout: str = "compact"
    short_name: str = Field("", title="Short name")
    state: State = Field("in_progress", enum_resolver=_states_enum, title="State")
    icon: str = Field("task_alt", title="Icon", widget="icon")


class DefaultSyncInfo(BaseSettingsModel):
    tasks: list[TaskCondition] = Field(default_factory=list, title="Tasks")
    status: list[StatusCondition] = Field(
        default_factory=list, title="Statuses"
    )


class SyncSettings(BaseSettingsModel):
    """
    Sync settings for Aquarium addon
    Defines default sync info for tasks and statuses
    """

    default: DefaultSyncInfo = Field(
        default_factory=DefaultSyncInfo,
        title="Default sync info",
    )


class AquariumSettings(BaseSettingsModel):
    """
    Aquarium addon settings
    Defines Aquarium URL and service settings
    """
    url: str = Field(
        "",
        placeholder="https://studio.aquarium.app",
        title="Aquarium URL",
        description="Enter your Aquarium URL",
    )

    domain: str | None = Field(
        None,
        placeholder="",
        title="Aquarium domain [optional]",
        description="Specify the domain used for unauthenticated requests. Mainly for Aquarium Fatfish Lab dev or local Aquarium server without DNS",
    )

    services: AquariumServiceSettings = Field(
        default_factory=AquariumServiceSettings, # type: ignore
        title="Service settings",
    )

    sync: SyncSettings = Field(
        default_factory=SyncSettings,
        title="Sync settings",
    )