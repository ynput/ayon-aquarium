from ayon_server.settings import BaseSettingsModel, SettingsField
from ayon_server.settings.enum import secrets_enum

from .publish import PublishPlugins, DEFAULT_PUBLISH_VALUES


class ServicesSettings(BaseSettingsModel):
    api_key: str = SettingsField(
        "aquarium_api_key",
        enum_resolver=secrets_enum,
        title="API key used in service",
    )
    # NOTE Don't know if is possible to provice consistent api
    #   key for services? Other way would be to set username/password
    # login_password: str = SettingsField(
    #     "aquarium_username",
    #     enum_resolver=secrets_enum,
    #     title="Aquarium username for service",
    #     scope=["studio"],
    # )
    # login_password: str = SettingsField(
    #     "aquarium_password",
    #     enum_resolver=secrets_enum,
    #     title="Aquarium password for service",
    #     scope=["studio"],
    # )


class AquariumSettings(BaseSettingsModel):
    enabled: bool = SettingsField(True)
    server_url: str = SettingsField(
        "",
        title="Aquarium Server",
        scope=["studio"],
    )
    # Uncomment when services are needed
    # services: ServicesSettings = SettingsField(
    #     default_factory=ServicesSettings,
    #     title="Services settings",
    #     scope=["studio"],
    # )
    publish: PublishPlugins = SettingsField(
        default_factory=PublishPlugins,
        title="Publish plugins",
    )


DEFAULT_VALUES = {
    "publish": DEFAULT_PUBLISH_VALUES
}
