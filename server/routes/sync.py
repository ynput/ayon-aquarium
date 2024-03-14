from typing import TYPE_CHECKING
from nxtools import logging
import asyncio
import hashlib
import time


from ayon_server.lib.postgres import Postgres
from ayon_server.entities import UserEntity, FolderEntity, TaskEntity
from ayon_server.events import dispatch_event, update_event
from ayon_server.types import Field, OPModel

from .anatomy import get_ayon_project
from .utils import get_folder_by_aquarium_key, get_task_by_aquarium_key, get_event_by_id

if TYPE_CHECKING:
    from .. import AquariumAddon

syncTopic = "aquarium.sync_project"

async def trigger_sync_project(addon: "AquariumAddon", project_name: str, user: "UserEntity", aquarium_project_key: str | None = None) -> str:
    """
        Create an event 'aquarium.sync_project' to sync a project from Aquarium to Ayon.
        The event will be processed by the processor service.
    """

    if aquarium_project_key is None:
        async for res in Postgres.iterate(
            "SELECT data->>'aquariumProjectKey' FROM projects WHERE name = $1",
            project_name,
        ):
            aquarium_project_key = res[0]

    # FIXME: Added timespamp to hash to avoid hash collision since restarting event doesn't seem to enroll in the processor
    hash = hashlib.sha256(
        f"aquarium_{time.time()}_{project_name}_{aquarium_project_key}".encode("utf-8")
    ).hexdigest()

    query = """
        SELECT id FROM events
        WHERE hash = $1
    """

    existingEvent = await Postgres.fetch(query, hash)
    if existingEvent:
        logging.info(f"Event {syncTopic} already exists and it's pending. Restarting it.")
        eventId = existingEvent[0][0]
        await update_event(
            eventId,
            description="Sync request from Aquarium",
            project=project_name,
            user=user.name,
        )

        await Postgres.execute(
            """
            UPDATE events SET
                updated_at = NOW(),
                status = 'restarted',
                retries = 0
            WHERE topic = $1
            AND depends_on = $2
            """,
            syncTopic,
            eventId,
        )
        return eventId
    else:
        eventId = await dispatch_event(
            syncTopic,
            hash=hash,
            description="Sync project from Aquarium to Ayon",
            project=project_name,
            user=user.name,
            payload={
                "aquariumProjectKey": aquarium_project_key,
            },
        )
        return eventId


class SyncProjectRequest(OPModel):
    eventId: str = Field(..., title="Event ID")
    items: dict = Field(..., title="Aquarium items, regrouped by type")

async def sync_project(addon: "AquariumAddon", project_name: str, user: "UserEntity", request: "SyncProjectRequest") -> str:
    """
        Sync project's items from Aquarium to Ayon.
    """

    eventId = request.eventId
    event = await get_event_by_id(eventId)
    def updateProgression(itemType: str, progression: float):
        event['summary'][itemType]['progression'] = round(progression, 2)
        asyncio.create_task(update_event(eventId, summary=event['summary']))


    project = await get_ayon_project(project_name)
    if project is None:
        logging.error(f"Can't sync project {project_name}. The project is not found on Ayon database.")
        return "Project not found"

    if not 'aquariumProjectKey' in project.data:
        logging.error(f"Can't sync project {project_name}. The project is not paired with an Aquarium project.")
        return "aquariumProjectKey not found"

    logging.info(f"Syncing project {project_name}...")

    items = request.items
    sync_order = ['Library', 'Asset', 'Episode', 'Sequence', 'Shot']
    for itemType in sync_order:
        # logging.debug(f"Processing {itemType} items...")
        if itemType in items:
            for item in items[itemType]:
                # logging.debug(f"  - Processing {item['folder']['name']}...")
                await sync_folder(addon, project_name, user, SyncFolderRequest(folder=item['folder'], path=item['path']))
                if "tasks" in item:
                    for task in item['tasks']:
                        # logging.debug(f"    - Processing {task['task']['name']}...")
                        await sync_task(addon, project_name, user, SyncTaskRequest(task=task['task'], path=task['path']))
                updateProgression(itemType, (items[itemType].index(item) + 1) / len(items[itemType]))

    logging.info(f"Project {project_name} synced")
    return project.name


class SyncFolderRequest(OPModel):
    folder: dict = Field(..., title="Folder entity")
    path: list = Field(..., title="Aquarium context path of the folder")

async def sync_folder(addon: "AquariumAddon", project_name: str, user: "UserEntity", request: SyncFolderRequest) -> str:
    """
        Sync a project's item from Aquarium as an Ayon folder.
    """
    folder = request.folder
    path = request.path
    saveRequired = False

    if not 'aquariumKey' in folder['data']:
        logging.error(f"Can't sync folder {folder['name']}. The aquariumKey is not found on the folder data.")
        return "aquariumKey not found"

    # QUESTION: To discuss with users, should we create all intermediate folders
    if path is not None:
        aqParent = path[1]
        parent = await get_folder_by_aquarium_key(project_name, aqParent["_key"])
        if parent is not None:
           folder['parentId'] = parent.id

    folderEntity = await get_folder_by_aquarium_key(project_name, folder['data']['aquariumKey'])

    # Folder already exists
    if folderEntity:
        if folder['name'] != folderEntity.name:
            setattr(folderEntity, 'name', folder['name'])
            saveRequired = True

        if folder['label'] != folderEntity.label:
            setattr(folderEntity, 'label', folder['label'])
            saveRequired = True

        for key, value in folder['attrib'].items():
            if not key in folderEntity.attrib or getattr(folderEntity.attrib, key) != value:
                setattr(folderEntity.attrib, key, value)
                if key not in folderEntity.own_attrib:
                    folderEntity.own_attrib.append(key)
                saveRequired = True
    else:
        try:
            folderEntity = FolderEntity(
                project_name=project_name,
                payload=folder,
            )
            saveRequired = True
        except Exception as e:
            logging.error(f"Error while creating folder {folder['name']} #{folder['data']['aquariumKey']}: {e}")
            return ''

    try:
        if saveRequired:
            await folderEntity.save()
        return folderEntity.id
    except Exception as e:
        logging.error(f"Error while saving folder {folder['name']} #{folder['data']['aquariumKey']}: {e}")
        return ''


class SyncTaskRequest(OPModel):
    task: dict = Field(..., title="Task entity")
    path: list = Field(..., title="Aquarium context path of the folder")

async def sync_task(addon: "AquariumAddon", project_name: str, user: "UserEntity", request: SyncTaskRequest) -> str:
    """
        Sync a task from Aquarium as an Ayon task.
        If the tasks's parent doesn't exist on Ayon, an error is raised.
    """
    task = request.task
    path = request.path
    saveRequired = False

    if path is not None:
        aqParent = path[1]
        parent = await get_folder_by_aquarium_key(project_name, aqParent["_key"])
        if parent is not None:
           task['folderId'] = parent.id

    if "folderId" not in task or task["folderId"] == None:
        logging.error(f"Can't sync task {task['name']} #{task['data']['aquariumKey']}. The folderId #{path[1]['_key']} is not found on Ayon database.")
        return "No folderId provided"

    project = await get_ayon_project(project_name)
    if not 'taskType' in task:
        for taskType in project.task_types:
            if taskType['name'].lower() == task['label'].lower() or taskType['name'].lower() == task['name'].lower():
                task['taskType'] = taskType['name']

    if not 'status' in task or task['status'] is None:
        task['status'] = project.statuses[0]['name']

    taskEntity = await get_task_by_aquarium_key(project_name, task['data']['aquariumKey'])

    # Task already exists
    if taskEntity:
        if task['name'] != taskEntity.name:
            setattr(taskEntity, 'name', task['name'])
            saveRequired = True

        if task['label'] != taskEntity.label:
            setattr(taskEntity, 'label', task['label'])
            saveRequired = True

        if task['status'] != taskEntity.status:
            setattr(taskEntity, 'status', task['status'])
            saveRequired = True

        if task['assignees'] != taskEntity.assignees:
            setattr(taskEntity, 'assignees', task['assignees'])
            saveRequired = True

        for key, value in task['attrib'].items():
            if not key in taskEntity.attrib or getattr(taskEntity.attrib, key) != value:
                setattr(taskEntity.attrib, key, value)
                if key not in taskEntity.own_attrib:
                    taskEntity.own_attrib.append(key)
                saveRequired = True
    else:
        try:
            taskEntity = TaskEntity(
                project_name=project_name,
                payload=task,
            )
            saveRequired = True
        except Exception as e:
            logging.error(f"Error while creating task {task['name']} #{task['data']['aquariumKey']}: {e}")
            return ''

    try:
        if saveRequired:
            await taskEntity.save()
        return taskEntity.id

    except Exception as e:
        logging.error(f"Error while saving task {task['name']} #{task['data']['aquariumKey']}: {e}")
        return ''
