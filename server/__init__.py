from typing import Type

from ayon_server.addons import BaseServerAddon, AddonLibrary

from .settings import AquariumSettings, DEFAULT_VALUES
from .version import __version__


class AquariumAddon(BaseServerAddon):
    name = "aquarium"
    title = "Aquarium"
    version = __version__
    settings_model: Type[AquariumSettings] = AquariumSettings
    # NOTE Uncomment when services are needed
    # services = {
    #     "leecher": {"image": f"ynput/ayon-aquarium-leecher:{__version__}"},
    #     "processor": {"image": f"ynput/ayon-aquarium-processor:{__version__}"}
    # }

    async def get_default_settings(self):
        settings_model_cls = self.get_settings_model()
        return settings_model_cls(**DEFAULT_VALUES)
