from ayon_server.settings import BaseSettingsModel, SettingsField


class CollectFamilyAdvancedFilterModel(BaseSettingsModel):
    _layout = "expanded"
    families: list[str] = SettingsField(
        default_factory=list,
        title="Additional Families"
    )
    add_aquarium_family: bool = SettingsField(
        True,
        title="Add Aquarium Family"
    )


class CollectFamilyProfile(BaseSettingsModel):
    _layout = "expanded"
    host_names: list[str] = SettingsField(
        default_factory=list,
        title="Host names",
    )
    product_types: list[str] = SettingsField(
        default_factory=list,
        title="Families",
    )
    task_types: list[str] = SettingsField(
        default_factory=list,
        title="Task types",
    )
    task_names: list[str] = SettingsField(
        default_factory=list,
        title="Task names",
    )
    add_aquarium_family: bool = SettingsField(
        True,
        title="Add Aquarium Family",
    )
    advanced_filtering: list[CollectFamilyAdvancedFilterModel] = SettingsField(
        title="Advanced adding if additional families present",
        default_factory=list,
    )


class CollectAquariumFamilyPlugin(BaseSettingsModel):
    _isGroup = True
    enabled: bool = True
    profiles: list[CollectFamilyProfile] = SettingsField(
        default_factory=list,
        title="Profiles",
    )


class PublishPlugins(BaseSettingsModel):
    CollectAquariumFamily: CollectAquariumFamilyPlugin = SettingsField(
        default_factory=CollectAquariumFamilyPlugin,
        title="Collect Aquarium Family"
    )


DEFAULT_PUBLISH_VALUES = {
    "CollectAquariumFamily":  {
        "enabled": True,
        "profiles": [
            {
                "host_names": [
                    "standalonepublisher"
                ],
                "product_types": [],
                "task_types": [],
                "task_names": [],
                "add_aquarium_family": True,
                "advanced_filtering": []
            },
            {
                "host_names": [
                    "standalonepublisher"
                ],
                "product_types": [
                    "matchmove",
                    "shot"
                ],
                "task_types": [],
                "task_names": [],
                "add_aquarium_family": False,
                "advanced_filtering": []
            },
            {
                "host_names": [
                    "standalonepublisher"
                ],
                "product_types": [
                    "plate"
                ],
                "task_types": [],
                "task_names": [],
                "add_aquarium_family": False,
                "advanced_filtering": [
                    {
                        "families": [
                            "clip",
                            "review"
                        ],
                        "add_aquarium_family": True
                    }
                ]
            },
            {
                "host_names": [
                    "traypublisher"
                ],
                "product_types": [],
                "task_types": [],
                "task_names": [],
                "add_aquarium_family": True,
                "advanced_filtering": []
            },
            {
                "host_names": [
                    "traypublisher"
                ],
                "product_types": [
                    "matchmove",
                    "shot"
                ],
                "task_types": [],
                "task_names": [],
                "add_aquarium_family": False,
                "advanced_filtering": []
            },
            {
                "host_names": [
                    "traypublisher"
                ],
                "product_types": [
                    "plate",
                    "review",
                    "audio"
                ],
                "task_types": [],
                "task_names": [],
                "add_aquarium_family": False,
                "advanced_filtering": [
                    {
                        "families": [
                            "clip",
                            "review"
                        ],
                        "add_aquarium_family": True
                    }
                ]
            },
            {
                "host_names": [
                    "maya"
                ],
                "product_types": [
                    "model",
                    "setdress",
                    "animation",
                    "look",
                    "rig",
                    "camera"
                ],
                "task_types": [],
                "task_names": [],
                "add_aquarium_family": True,
                "advanced_filtering": []
            },
            {
                "host_names": [
                    "tvpaint"
                ],
                "product_types": [
                    "renderPass"
                ],
                "task_types": [],
                "task_names": [],
                "add_aquarium_family": False,
                "advanced_filtering": []
            },
            {
                "host_names": [
                    "tvpaint"
                ],
                "product_types": [],
                "task_types": [],
                "task_names": [],
                "add_aquarium_family": True,
                "advanced_filtering": []
            },
            {
                "host_names": [
                    "nuke"
                ],
                "product_types": [
                    "write",
                    "render",
                    "prerender"
                ],
                "task_types": [],
                "task_names": [],
                "add_aquarium_family": False,
                "advanced_filtering": [
                    {
                        "families": [
                            "review"
                        ],
                        "add_aquarium_family": True
                    }
                ]
            },
            {
                "host_names": [
                    "aftereffects"
                ],
                "product_types": [
                    "render",
                    "workfile"
                ],
                "task_types": [],
                "task_names": [],
                "add_aquarium_family": True,
                "advanced_filtering": []
            },
            {
                "host_names": [
                    "flame"
                ],
                "product_types": [
                    "plate",
                    "take"
                ],
                "task_types": [],
                "task_names": [],
                "add_aquarium_family": True,
                "advanced_filtering": []
            },
            {
                "host_names": [
                    "houdini"
                ],
                "product_types": [
                    "usd"
                ],
                "task_types": [],
                "task_names": [],
                "add_aquarium_family": True,
                "advanced_filtering": []
            },
            {
                "host_names": [
                    "photoshop"
                ],
                "product_types": [
                    "review"
                ],
                "task_types": [],
                "task_names": [],
                "add_aquarium_family": True,
                "advanced_filtering": []
            }
        ]
    }
}
