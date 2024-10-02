"""Aquarium addon."""

import os
import sys

from ayon_core.addon import (
    AYONAddon,
    IPluginPaths,
    ITrayAction,
)
from .version import __version__

AQUARIUM_ADDON_DIR = os.path.dirname(os.path.abspath(__file__))
vendorsPath = os.path.join(AQUARIUM_ADDON_DIR, "vendors")
if vendorsPath not in sys.path:
    sys.path.append(vendorsPath)

class AquariumAddon(AYONAddon, IPluginPaths, ITrayAction):
    """Aquarium addon class."""

    label = "Aquarium"
    name = "aquarium"
    version = __version__

    def initialize(self, settings):
        aquarium_settings = settings[self.name]

        self._url = aquarium_settings["url"].strip()
        self._domain = aquarium_settings["domain"].strip()

        self._dialog = None

    def get_global_environments(self):
        """Aquarium global environments."""

        return {
            "AQUARIUM_SERVER_URL": self._url,
            "AQUARIUM_DOMAIN": self._domain
        }

    def get_aquarium_url(self):
        """Resolved Aquarium url.

        Resolving is trying to fill missing information in url and tried to
        connect to the server.

        Returns:
            Union[str, None]: Final variant of url or None if url could not be
                reached.
        """

        return self._url

    url = property(get_aquarium_url)

    def tray_init(self):
        """Tray init."""

        pass

    def tray_start(self):
        """Tray start."""
        from .credentials import (
            load_credentials,
            validate_credentials,
            set_credentials_envs,
        )

        token = load_credentials()

        # Check credentials, ask them if needed
        if validate_credentials(token):
            set_credentials_envs(token)
        else:
            self.show_signin()

    def _get_dialog(self):
        if self._dialog is None:
            from .login_dialog import AquariumCredentialsDialog

            self._dialog = AquariumCredentialsDialog(self)

        return self._dialog

    def show_signin(self):
        """Show dialog to log-in."""

        # Make sure dialog is created
        dialog = self._get_dialog()

        # Show dialog
        dialog.open()

    def on_action_trigger(self):
        """Implementation of abstract method for `ITrayAction`."""
        self.show_signin()

    def get_plugin_paths(self):
        """Implementation of abstract method for `IPluginPaths`."""
        print([os.path.join(AQUARIUM_ADDON_DIR, "plugins", "launcher")])
        return {
            "publish": self.get_publish_plugin_paths(),
            # The laucher action is not working since AYON conversion
            "actions": [os.path.join(AQUARIUM_ADDON_DIR, "plugins", "launcher")],
        }

    def get_publish_plugin_paths(self, host_name=None):
        return [os.path.join(AQUARIUM_ADDON_DIR, "plugins", "publish")]
