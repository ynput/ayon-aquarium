import copy

import pyblish.api

from ayon_aquarium.pipeline import plugin


class IntegrateHierarchyToAquarium(plugin.AquariumPublishContextPlugin):
    """Create entities in aquarium based on collected data from editorial.

    Example of entry data:
    {
        "ProjectXS": {
            "entity_type": "Project",
            "custom_attributes": {
                "fps": 24,...
            },
            "tasks": [
                "Compositing",
                "Lighting",... *task must exist as task type in project schema*
            ],
            "childs": {
                "sq01": {
                    "entity_type": "Sequence",
                    ...
                }
            }
        }
    }
    """

    order = pyblish.api.IntegratorOrder - 0.04
    label = "Integrate Hierarchy To Aquarium"
    families = ["shot"]
    hosts = [
        "hiero",
        "resolve",
        "standalonepublisher",
        "flame",
        "traypublisher"
    ]
    optional = False
    create_task_status_profiles = []

    def process(self, context):
        if "hierarchyContext" not in context.data:
            return

        hierarchy_context = copy.deepcopy(context.data["hierarchyContext"])
        # TODO imlement
