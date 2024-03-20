import webbrowser
import ayon_api

from urllib.parse import urlencode, urljoin
try:
    from openpype.pipeline import LauncherAction
    from openpype.modules import ModulesManager
except ImportError:
    from ayon_core.pipeline import LauncherAction
    from ayon_core.modules import ModulesManager


class ShowInAquarium(LauncherAction):
    name = "showinaquarium"
    label = "Show in Aquarium"
    icon = "external-link-square"
    # icon = "aquarium-icon.png"
    # color = "#339af0"
    order = 10

    @staticmethod
    def get_aquarium_module():
        print('GET AQUARIUM MODULE')
        return ModulesManager().modules_by_name.get("aquarium")

    def is_compatible(self, session):
        print(session)
        if not session.get("AVALON_PROJECT"):
            return False
        return True

    def process(self, session, **kwargs):
        # Context inputs
        print(session)
        project_name = session["AVALON_PROJECT"]
        asset_name = session.get("AVALON_ASSET", None)
        task_name = session.get("AVALON_TASK", None)

        project = ayon_api.get_project(project_name)
        if not project:
            raise RuntimeError("Project {} not found.".format(project_name))

        project_aquarium_key = project["data"].get("aquariumProjectKey", None)
        if not project_aquarium_key:
            raise RuntimeError(
                "Project {} has no paired with an Aquarium project.".format(project_name)
            )

        # https://fatfishlab.aquarium.app/open/1234
        # http://localhost:3000/apps/asseteditor?itemKeys=252552&mediaIndex=1&historyIndex=1&tabName=viewer&taskName=Me&versionIndex=1
        entity = ayon_api.get_folder_by_name(project_name, asset_name)
        if not entity:
            raise RuntimeError("Entity {} not found.".format(asset_name))

        # Get Aquarium item._key
        itemKey = entity["data"].get("aquariumKey", None)
        if not itemKey:
            raise RuntimeError("Entity {} has no paired with an Aquarium item.".format(asset_name))

        # Get Aquarium task._key
        task = ayon_api.get_task_by_name(project_name, entity["_id"], task_name)
        if not task:
            raise RuntimeError("Task {} not found.".format(task_name))

        taskKey = task["data"].get("aquariumKey", None)
        if not taskKey:
            raise RuntimeError("Task {} has no paired with an Aquarium task.".format(task_name))

        appName = None
        if entity["type"] in ["Episode", "Sequence", "Shot"]:
            appName = "shoteditor"
        elif entity["type"] in ["Library", "Asset"]:
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
        aq = self.get_aquarium_module()

        # Get aquarium url with /api stripped
        aquarium_url = aq.api_url
        query = urlencode(kwargs)
        url = urljoin(aquarium_url, f"/apps/{appName}?{query}")

        return url

    def generate_open_url(
        self,
        itemKey
    ):
        aq = self.get_aquarium_module()

        # Get aquarium url with /api stripped
        aquarium_url = aq.api_url
        url = urljoin(aquarium_url, f"/open/{itemKey}")

        return url
