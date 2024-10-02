import webbrowser
import ayon_api

from urllib.parse import urlencode, urljoin
from ayon_core.pipeline import LauncherAction
from ayon_core.addon import AddonsManager


class ShowInAquarium(LauncherAction):
    name = "showinaquarium"
    label = "Show in Aquarium"
    icon = "external-link-square"
    # icon = "aquarium-icon.png"
    # color = "#339af0"
    order = 10

    @staticmethod
    def get_aquarium_addon():
        print('GET AQUARIUM ADDON')
        return AddonsManager().get("aquarium")

    def is_compatible(self, selection):
        return selection.is_task_selected

    def process(self, selection, **kwargs):
        project_name = selection.get_project_name()
        project = selection.get_project_entity()
        project_aquarium_key = project["data"].get("aquariumProjectKey", None)
        if not project_aquarium_key:
            raise RuntimeError(
                f"Project {project_name} has no paired with"
                " an Aquarium project."
            )

        # https://fatfishlab.aquarium.app/open/1234
        # http://localhost:3000/apps/asseteditor?itemKeys=252552&mediaIndex=1&historyIndex=1&tabName=viewer&taskName=Me&versionIndex=1
        folder_entity = selection.get_folder_entity()
        task_entity = selection.get_task_entity()

        folder_path = folder_entity["path"]
        # Get Aquarium item._key
        itemKey = folder_entity["data"].get("aquariumKey", None)
        if not itemKey:
            raise RuntimeError(
                f"Folder {folder_path} has no paired with an Aquarium item."
            )

        # Get Aquarium task._key
        taskKey = task_entity["data"].get("aquariumKey", None)
        if not taskKey:
            raise RuntimeError(
                f"Task {folder_path}/{task_entity['name']} has"
                " no paired with an Aquarium task."
            )

        appName = None
        if folder_entity["folderType"] in ["Episode", "Sequence", "Shot"]:
            appName = "shoteditor"
        elif folder_entity["folderType"] in ["Library", "Asset"]:
            appName = "asseteditor"

        # Define URL
        if appName:
            url = self.generate_standalone_url(
                appName,
                itemKeys=itemKey,
                taskName=taskKey,
            )
        else:
            url = self.generate_open_url(
                itemKey
            )

            # Open URL in webbrowser
        self.log.info("Opening URL: {}".format(url))
        webbrowser.open(
            url,
            # Try in new tab
            new=2,
        )

    def generate_standalone_url(
        self,
        appName,
        *args,
        **kwargs,
    ):
        aq = self.get_aquarium_addon()

        # Get aquarium url with /api stripped
        aquarium_url = aq.api_url
        query = urlencode(kwargs)
        url = urljoin(aquarium_url, f"/apps/{appName}?{query}")

        return url

    def generate_open_url(
        self,
        itemKey
    ):
        aq = self.get_aquarium_addon()

        # Get aquarium url with /api stripped
        aquarium_url = aq.api_url
        url = urljoin(aquarium_url, f"/open/{itemKey}")

        return url
