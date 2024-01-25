import os

from openpype.modules import (
    AYONAddon,
    ITrayModule,
    IPluginPaths,
)

AQUARIUM_ADDON_DIR = os.path.dirname(os.path.abspath(__file__))


class AquariumAddon(
    AYONAddon,
    ITrayModule,
    IPluginPaths,
):
    name = "aquarium"

    def initialize(self, settings):
        addon_settings = settings[self.name]

        self._aquarium_url = addon_settings["server_url"]

        self._tray_wrapper = None

    def get_global_environments(self):
        """Aquarium global environments."""

        return {
            "AQUARIUM_SERVER_URL": self._aquarium_url
        }

    def get_aquarium_url(self):
        """Resolved ftrack url.

        Resolving is trying to fill missing information in url and tried to
        connect to the server.

        Returns:
            Union[str, None]: Final variant of url or None if url could not be
                reached.
        """

        return self._aquarium_url

    aquarium_url = property(get_aquarium_url)

    def get_plugin_paths(self):
        """Ftrack plugin paths."""
        return {
            "publish": [
                os.path.join(AQUARIUM_ADDON_DIR, "plugins", "publish")
            ]
        }

    def get_launch_hook_paths(self):
        """Implementation for applications launch hooks."""

        return os.path.join(AQUARIUM_ADDON_DIR, "launch_hooks")

    def tray_init(self):
        from .tray_wrap import AquariumTrayWrapper

        self._tray_wrapper = AquariumTrayWrapper(self)

    def tray_menu(self, parent_menu):
        return self._tray_wrapper.tray_menu(parent_menu)

    def tray_start(self):
        return self._tray_wrapper.validate()

    def tray_exit(self):
        self._tray_wrapper.tray_exit()

    def set_credentials_to_env(self, api_key):
        os.environ["AQUARIUM_API_KEY"] = api_key or ""

    def get_credentials(self):
        """Get local Ftrack credentials."""

        from .credentials import get_credentials

        cred = get_credentials(self.ftrack_url)
        return cred.get("api_key")

