import pyblish.api

from ayon_aquarium.pipeline import plugin


class IntegrateAquariumInstance(plugin.AquariumPublishInstancePlugin):
    """Integrate instances to aquarium.

    Plugin should upload reviewables based on instance data and it's context,
        also can upload thumbnails and add paths of integrated components.
    """

    order = pyblish.api.IntegratorOrder + 0.48
    label = "Integrate Aquarium Components"
    families = ["aquarium"]

    def process(self, instance):
        # TODO implement
        #  Integrate review and maybe other components to aquarium
        #  - I don't know capabalities of aquarium
        pass
