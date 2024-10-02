"""
Requires:
    none

Provides:
    instance     -> families ([])
"""
import pyblish.api

from ayon_core.lib import filter_profiles

from ayon_aquarium.pipeline import plugin


class CollectAquariumFamily(plugin.AquariumPublishInstancePlugin):
    """Adds explicitly 'aquarium' family to integrate instance to aquarium.

    Uses selection by combination of hosts/families/tasks names via
    profiles resolution.

    Triggered everywhere, checks instance against configured.

    Checks advanced filtering which works on 'families' not on main
    'family', as some variants dynamically resolves addition of aquarium
    based on 'families' (editorial drives it by presence of 'review')
    """

    label = "Collect Aquarium Family"
    order = pyblish.api.CollectorOrder + 0.4990

    profiles = None

    def process(self, instance):
        if not self.profiles:
            self.log.warning("No profiles present for adding aquarium family")
            return

        host_name = instance.context.data["hostName"]
        family = instance.data["family"]
        task_name = instance.data.get("task")

        filtering_criteria = {
            "host_names": host_name,
            "product_types": family,
            "task_names": task_name
        }
        profile = filter_profiles(
            self.profiles,
            filtering_criteria,
            logger=self.log
        )

        add_aquarium_family = False
        families = instance.data.setdefault("families", [])

        if profile:
            add_aquarium_family = profile["add_aquarium_family"]
            additional_filters = profile.get("advanced_filtering")
            if additional_filters:
                families_set = set(families) | {family}
                self.log.info(
                    "'{}' families used for additional filtering".format(
                        families_set))
                add_aquarium_family = self._additional_filtering(
                    additional_filters,
                    families_set,
                    add_aquarium_family
                )

        result_str = "Not adding"
        if add_aquarium_family:
            result_str = "Adding"
            if "aquarium" not in families:
                families.append("aquarium")

        self.log.debug("{} 'aquarium' family for instance with '{}'".format(
            result_str, family
        ))

    def _additional_filtering(
        self, additional_filters, families, add_aquarium_family
    ):
        """Compares additional filters - working on instance's families.

        Triggered for more detailed filtering when main family matches,
        but content of 'families' actually matter.
        (For example 'review' in 'families' should result in adding to
        aquarium)

        Args:
            additional_filters (dict): Additional filtering from Setting.
            families (set[str]): All instance families.
            add_aquarium_family (bool): Add 'aquarium' to families if True.

        Returns:
            bool: Aquarium family should be added.
        """

        override_filter = None
        override_filter_value = -1
        for additional_filter in additional_filters:
            filter_families = set(additional_filter["families"])
            valid = filter_families <= set(families)  # issubset
            if not valid:
                continue

            value = len(filter_families)
            if value > override_filter_value:
                override_filter = additional_filter
                override_filter_value = value

        if override_filter:
            add_aquarium_family = override_filter["add_aquarium_family"]

        return add_aquarium_family
