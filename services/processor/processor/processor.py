import time
import queue
import logging

from ayon_api import (
    get,
    get_service_addon_name,
    get_service_addon_version,
    enroll_event_job,
    get_event,
    update_event,
)

from aquarium_common import AquariumServices, connect_to_ayon, register_signals
from .handlers import (
    sequences,
    projects,
    episodes,
    assets,
    shots,
    tasks,
)

log = logging.getLogger(__name__)
_AQS = AquariumServices()

# Aquarium processor class
class AquariumProcessor():
    """
        Aquarium processor is responsible for processing events from the leecher
        with the appropriate handler. The processor is also responsible for transforming
        Aquarium structure to Ayon structure. The "Ayonisation" is done in the handlers.
    """

    _events_queue = queue.Queue()

    pairing_list = []
    handlers = []
    processing = False

    addon_name = None
    addon_version = None
    entrypoint = None

    def __init__(self, parent: "AquariumServices"):
        self.addon_name = get_service_addon_name()
        self.addon_version = get_service_addon_version()
        self.entrypoint = f"/addons/{self.addon_name}/{self.addon_version}"

        self._AQS = parent
        self.processing = False

        self.pairing_list = self.get_pairing_list()

    def get_next_aquarium_event(self):
        """Full project sync is prioritized over other events."""

        return enroll_event_job(
            source_topic="aquarium.sync_project",
            target_topic="aquarium.process",
            sender=get_service_addon_name(),
            description="Processing sync project",
            sequential=True
        ) or enroll_event_job(
            source_topic="aquarium.project_create",
            target_topic="aquarium.process",
            sender=get_service_addon_name(),
            description="Processing create Aquarium project",
            sequential=True
        ) or enroll_event_job(
            source_topic="aquarium.leech",
            target_topic="aquarium.process",
            sender=get_service_addon_name(),
            description="Event processing",
            sequential=True
        )

    def load_event_from_jobs(self):
        job = self.get_next_aquarium_event()
        if not job:
            return False

        event = get_event(job["dependsOn"])
        self._events_queue.put((event, job))
        return True

    def wait(self, duration=None):
        """Overridden wait
        Event are loaded from Mongo DB when queue is empty. Handled event is
        set as processed in Mongo DB.
        """

        self.processing = True
        started = time.time()
        log.info("Processor listening loop started")
        while self.processing:
            job = None
            try:
                item = self._events_queue.get(timeout=0.5)
                if isinstance(item, tuple):
                    rawEvent, job = item
                else:
                    rawEvent = item

            except queue.Empty:
                if not self.load_event_from_jobs():
                    time.sleep(0.1)
                continue

            self.set_job_processing(job)

            self.process_event(rawEvent, job)

            if job is not None:
                self.set_job_finished(job)

            if duration is not None:
                if (time.time() - started) > duration:
                    break

    def process_event(self, rawEvent: dict, job):
        ayonTopic = rawEvent["topic"]
        log.info(f"Processing event: {ayonTopic}")

        if ayonTopic in self._AQS.IGNORE_TOPICS:
            return

        # QUESTION: Does the events need to trigger a full patch or a partial one ?
        # For example an updated event only sync updated data or all data ?
        # TODO: Users are not synced yet. Need to be checked with users before.
        if ayonTopic == 'aquarium.sync_project':
            projects.sync(self, rawEvent["payload"]['aquariumProjectKey'], job.get('dependsOn', ''))
        if ayonTopic == 'aquarium.project_create':
            projects.create(self, rawEvent["payload"]['aquariumProjectName'], rawEvent["project"])
        elif ayonTopic == 'aquarium.leech':
            event = self._AQS.aq.event(rawEvent["payload"])
            if event.topic == 'item.updated.Project':
                projects.updated(self, event)
            elif event.topic == 'item.created.Asset':
                assets.created(self, event)
            elif event.topic == 'item.updated.Asset':
                assets.updated(self, event)
            elif event.topic == 'item.created.Shot':
                shots.created(self, event)
            elif event.topic == 'item.updated.Shot':
                shots.updated(self, event)
            elif event.topic == 'item.created.Sequence':
                sequences.created(self, event)
            elif event.topic == 'item.updated.Sequence':
                sequences.updated(self, event)
            elif event.topic == 'item.created.Episode':
                episodes.created(self, event)
            elif event.topic == 'item.updated.Episode':
                episodes.updated(self, event)
            elif event.topic == 'item.created.Task':
                tasks.created(self, event)
            elif event.topic == 'item.updated.Task':
                tasks.updated(self, event)
            elif event.topic == 'user.assigned' or event.topic == 'user.unassigned':
                tasks.assigned(self, event)

    def set_job_processing(self, job):
        event_id = job["id"]
        source_id = job["dependsOn"]
        source_event = get_event(event_id)

        description = f"Processing {source_event['description']}"

        update_event(
            event_id,
            sender=get_service_addon_name(),
            status="in_progress",
            description=description,
        )

    def set_job_finished(self, job):
        event_id = job["id"]
        source_id = job["dependsOn"]
        source_event = get_event(event_id)
        description = f"Processed {source_event['description']}"

        update_event(
            event_id,
            sender=get_service_addon_name(),
            status="finished",
            description=description,
        )

    def get_paired_ayon_project(self, aq_project_key: str, retry=True):
        """Get the Ayon project name if paired"""

        for pair in self.pairing_list:
            if pair["aquariumProjectKey"] == aq_project_key:
                return pair["ayonProjectName"]

        if retry:
            self.pairing_list = self.get_pairing_list()
            return self.get_paired_ayon_project(aq_project_key, False)

    def get_pairing_list(self):
        """Get the list of paired projects between Aquarium and Ayon"""
        res = get(f"{self.entrypoint}/projects/pair")
        return res.data

    def stop(self):
        self.processing = False


def main():
    logging.basicConfig(level=logging.INFO)

    connect_to_ayon()
    register_signals(_AQS)

    while not _AQS.connected:
        _AQS.connect()
        if _AQS.connected is False:
            time.sleep(10)
            continue

        _AQS.session_fail_logged = False
        _AQS.processor = AquariumProcessor(_AQS) # type: ignore

        _AQS.processor.wait()
