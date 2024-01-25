import pyblish.api
from openpype.pipeline.publish import (
    get_plugin_settings,
    apply_plugin_settings_automatically,
)
from ayon_aquarium import is_aquarium_enabled_in_settings

SETTINGS_CATEGORY = "aquarium"


class AquariumPublishContextPlugin(pyblish.api.ContextPlugin):
    settings_category = SETTINGS_CATEGORY

    @classmethod
    def is_aquarium_enabled(cls, project_settings):
        return is_aquarium_enabled_in_settings(
            project_settings.get(SETTINGS_CATEGORY) or {}
        )

    @classmethod
    def apply_settings(cls, project_settings):
        if not cls.is_aquarium_enabled(project_settings):
            cls.enabled = False
            return

        plugin_settins = get_plugin_settings(
            cls, project_settings, cls.log, None
        )
        apply_plugin_settings_automatically(cls, plugin_settins, cls.log)


class AquariumPublishInstancePlugin(pyblish.api.InstancePlugin):
    settings_category = SETTINGS_CATEGORY

    @classmethod
    def is_aquarium_enabled(cls, project_settings):
        return is_aquarium_enabled_in_settings(
            project_settings.get(SETTINGS_CATEGORY) or {}
        )

    @classmethod
    def apply_settings(cls, project_settings):
        if not cls.is_aquarium_enabled(project_settings):
            cls.enabled = False
            return

        plugin_settins = get_plugin_settings(
            cls, project_settings, cls.log, None
        )
        apply_plugin_settings_automatically(cls, plugin_settins, cls.log)
