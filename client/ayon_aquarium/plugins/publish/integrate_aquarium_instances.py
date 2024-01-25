import os
import json
import copy
import pyblish.api

from openpype.pipeline.publish import get_publish_repre_path
from openpype.lib.openpype_version import get_openpype_version
from openpype.lib.transcoding import (
    get_ffprobe_streams,
    convert_ffprobe_fps_to_float,
)
from openpype.lib.profiles_filtering import filter_profiles
from openpype.lib.transcoding import VIDEO_EXTENSIONS

from ayon_ftrack.pipeline import plugin


class IntegrateFtrackInstance(plugin.FtrackPublishInstancePlugin):
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
