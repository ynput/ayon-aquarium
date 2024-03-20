from typing import TYPE_CHECKING, List, Dict, Any

# import json # DEBUG
import ayon_api
import logging
from uuid import uuid4
from copy import deepcopy, copy
from functools import reduce

from .utils import ayonise_folder, ayonise_task

if TYPE_CHECKING:
    from ..processor import AquariumProcessor

log = logging.getLogger(__name__)

def updated(processor: "AquariumProcessor", event):
    log.info(f"Update projet {event.data.item.data.name}")
    projectKey = event.data.item._key
    project_name = processor.get_paired_ayon_project(projectKey)
    if not project_name:
        return  # do nothing as aquarium and ayon project are not paired

    attributes = ayon_api.get(
        f"{processor.entrypoint}/projects/{project_name}/anatomy/attributes"
    )

    payload = {
        "attrib": attributes.data,
    }

    ayon_api.patch(
        f"/projects/{project_name}",
        json=payload
    )

def sync(processor: "AquariumProcessor", aquariumProjectKey: str, eventId: str):
    log.info(f"Gathering data for sync project #{aquariumProjectKey}...")
    project_name = processor.get_paired_ayon_project(aquariumProjectKey)
    if not project_name:
        return  # do nothing as aquarium and ayon project are not paired

    query = "# -($Child, 3)> 0,1000 item.type IN ['Episode', 'Sequence', 'Shot', 'Library', 'Asset'] SET $set COLLECT type = item.type INTO items = $items SORT null VIEW $view"
    aliases = {
        "set": {
            "mainPath": "path.vertices",
        },
        "items": {
            "folder": "item",
            "tasks": "# -($Child)> $Task SORT null VIEW $taskView",
            "path": "REVERSE(mainPath)" # REVERSE the path to match event path order
        },
        "taskView": {
            "task": "item",
            "assignees": "# -($Assigned)> $User SORT null VIEW item.data.email",
            "path": "REVERSE(APPEND(mainPath, SHIFT(path.vertices)))" # REVERSE to match event path order and SHIFT to avoid item deduplication
        },
        "view": {
            "type": "type",
            "items": "items"
        }
    }
    collections: list = processor._AQS.aq.project(aquariumProjectKey).traverse(meshql=query, aliases=aliases)
    log.info(f"{len(collections)} items type found for project #{aquariumProjectKey}.")

    items = {}
    eventSummary = {}
    cast = processor._AQS.aq.cast
    for itemType in collections:
        log.debug(f"Processing {itemType['type']} items...")
        items[itemType["type"]] = []
        for item in itemType["items"]:
            log.debug(f"  - Processing {item['folder']['data']['name']}...")
            items[itemType["type"]].append({
                "folder": ayonise_folder(cast(item['folder'])),
                "tasks": [dict(task=ayonise_task(cast(task["task"]), task['assignees']), path=task["path"]) for task in item['tasks']],
                "path": item['path']
            })

            # items[itemType["type"]] = [{folder, tasks: []}]
        eventSummary[itemType["type"]] = {
            "count": reduce(lambda count, item: count + 1 + len(item["tasks"]), items[itemType["type"]], 0),
            "error": None,
            "progression": 0
        }

    ayon_api.update_event(
        eventId,
        sender=ayon_api.get_service_addon_name(),
        summary=eventSummary
    )

    res = ayon_api.post(
        f"{processor.entrypoint}/projects/{project_name}/sync/all",
        items=items,
        eventId=eventId
    )

    try:
        res.raise_for_status()
        log.info(f"Sync data processed and submitted for project #{aquariumProjectKey}.")
    except Exception as e:
        log.error(f"Error while syncing project {aquariumProjectKey} to Ayon: {e}")
        return

def create(processor: "AquariumProcessor", aquariumProjectName: str, ayonProjectName: str):
    log.info(f"Creating project {ayonProjectName} on Aquarium...")

    hierarchy = ayon_api.get('projects/{project_name}/hierarchy'.format(project_name=ayonProjectName), types="Folder,Library,Asset,Episode,Sequence,Shot")
    hierarchy.raise_for_status()

    log.info(hierarchy.data.get('detail'))
    items = convert_hierarchy(hierarchy.data.get('hierarchy', []))

    # Create project
    attributes = ayon_api.get(
        f"{processor.entrypoint}/projects/{ayonProjectName}/anatomy/attributes"
    ).data
    project = dict(
        type="Project",
        data={
            "name": aquariumProjectName or ayonProjectName,
            "ayonProjectName": ayonProjectName,
            "startdate": attributes.get("startDate", None),
            "deadline": attributes.get("endDate", None),
            "description": attributes.get("description", None),
            "discardedAssistants": list()
        }
    )

    # Flatten and create edges
    aqJson = dict(items=[project], edges=list())

    def flatten(itemsToFlatten, _from = None):
        for index, item in enumerate(itemsToFlatten):
            if item.type == 'Shot':
                if 'setupShots' not in project['data']['discardedAssistants']: # type: ignore
                    project['data']['discardedAssistants'].append('setupShots') # type: ignore
            elif item.type == 'Asset':
                if 'setupAssets' not in project['data']['discardedAssistants']: # type: ignore
                    project['data']['discardedAssistants'].append('setupAssets') # type: ignore

            aqJson["items"].append(item.to_dict())
            _to = len(aqJson["items"]) - 1
            if _from is not None:
                aqJson["edges"].append({'type': "Child", '_from': _from, '_to': _to, "createdFrom": f"{item.createdFrom}-child", "data": { "weight": (index + 1) * 1000}}) # type: ignore

            if _from == 0 and item.type == 'Group':
                aqJson["edges"].append({'type': "Shortcut", '_from': _from, '_to': _to, "data": {}}) # type: ignore

            if item.type != 'Template':
                templateTuple = next((template for template in enumerate(aqJson['items']) if template[1]['type'] == 'Template' and template[1]['createdFrom'] == item.createdFrom), None)
                if templateTuple is not None:
                    aqJson["edges"].append({'type': "Template", '_from': templateTuple[0], '_to': _to, "data": {}}) # type: ignore

            if hasattr(item, 'children'):
                flatten(item.children, _to)

    log.info(f"Flattening hierarchy...")
    flatten(items, 0)

    # DEBUG: Write JSON to file
    # with open('/service/processor/output.json', 'w') as f:
    #     f.write(json.dumps(aqJson, indent=4))
    #     raise Exception("JSON written to file")

    # Link the bot to the project to display it in project settings
    log.info(f"Importing JSON on Aquarium ({len(aqJson['items'])} items, {len(aqJson['edges'])} edges)...")
    imported: Dict[str, List[Dict[str, Any]]] = processor._AQS.aq.do_request('POST', f"items/{processor._AQS.bot_key}/import/json", json=aqJson) # type: ignore


    if 'items' in imported and len(imported['items']) > 0:
        # FIXME: Need to exclude the creation of the project in the listenner to avoid double sync
        processor._AQS.aq.edge.create(type='Ayon', from_key=imported['items'][0]['_key'], to_key=processor._AQS.bot_key)
        ayon_api.patch(
            f"/projects/{ayonProjectName}",
            data={
                "aquariumProjectKey": imported['items'][0]['_key'],
            }
        )

    log.info(f"Project {ayonProjectName} created on Aquarium.")


def convert_hierarchy(hierarchy):
    class aqItem:
        def __init__(self, type, ayonId = None, data = dict(), parentId= None, createdFrom = None, children = None):
            self.data = data
            self.createdFrom = createdFrom or str(uuid4())
            self.children = children or list()
            self.ayonId = ayonId
            self.parentId = parentId

            if type == 'Folder':
                self.type = 'Group'
            else:
                self.type = type

        def __repr__(self):
            return f"{self.type} {self.data}, children: {self.children}"

        def to_dict(self):
            data = self.data.copy()
            data.update({"ayonId": self.ayonId})
            return {
                "type": self.type,
                "data": data,
                "createdFrom": self.createdFrom,
            }

    # Generate Aquarium templates
    def templatize(templates, entity):
        if entity['folderType'] in ['Folder', 'Task']:
            return templates

        templateWithSameType = [template for template in templates if template.data['templateData']['type'] == entity["folderType"]]
        existingTemplate = next((template for template in templateWithSameType if all(task.data['name'] in entity['taskNames'] for task in template.children)), None)

        if not existingTemplate:
            parentName = next((ayonEntity['label'].capitalize() for ayonEntity in hierarchy if ayonEntity['id'] == entity['parentId']), None)
            if entity["folderType"] not in templates and entity['folderType'] != 'Folder':
                templateData=dict(
                    name=f"{parentName or entity['folderType']} template",
                    description=f"Template with {', '.join(entity['taskNames'])}",
                    templateData={
                        "type": entity["folderType"].capitalize(),
                    })
                template = aqItem('Template', data=templateData)
                templates.append(template)

            if entity.get('hasTasks', False):
                for taskName in entity["taskNames"]:
                    template.children.append(aqItem('Task', data={"name": taskName}))

        return templates

    aqTemplates = reduce(templatize, hierarchy, list())
    log.info(f"Found {len(aqTemplates)} templates.")

    def find_parent(items, parentId):
        for item in items:
            if item.ayonId == parentId:
                return item
            elif hasattr(item, 'children'):
                found = find_parent(item.children, parentId)
                if found is not None:
                    return found
        return None

    # Convert to items, using templates if needed
    items = list()
    orphans = list()
    log.info(f"Creating hierarchy object with {len(hierarchy)} entities...")
    for entity in hierarchy:
        createdFrom = None
        tasks = []

        # Try to find the template for the entity based on its type and tasks names
        template = next((template for template in aqTemplates if template.data['templateData']['type'] == entity["folderType"] and all(task.data["name"] in entity["taskNames"] for task in template.children)), None)
        if template:
            createdFrom = template.createdFrom

        for taskName in entity["taskNames"]:
            # QUESTION: Hierarchy doesn't return task.id, so we can't add ayonId to the task. Snif.
            # Can I create a PR ?
            # ayonTask = next((ayonTask for ayonTask in hierarchy if ayonTask['taskType']))
            if template:
                templateTask = next((task for task in template.children if task.data["name"] == taskName), None)
                if templateTask:
                    task = deepcopy(templateTask)
                    # task.data["ayonId"] = ayonTask["id"]
                    tasks.append(task)
            else:
                # tasks.append(aqItem('Task', data={"name": taskName}, ayonId=ayonTask["id"]))
                tasks.append(aqItem('Task', data={"name": taskName}))

        item = aqItem(
            type=entity["folderType"],
            ayonId=entity["id"],
            parentId=entity["parentId"],
            data={"name": entity["label"]},
            createdFrom=createdFrom,
            children=tasks)

        if (entity["parentId"] == None):
            items.append(item)
        else:
            parent = find_parent(items, entity["parentId"])
            if parent:
                parent.children.append(item)
            else:
                orphans.append(item)

    # Move orphans to their parent
    for orphan in orphans:
        parent = find_parent(items, orphan.parentId)
        if parent:
            parent.children.append(orphan)
        else:
            log.warning(f"Orphan {orphan} has no parent, skipping")
            continue

    # Insert templates at the beginning
    for template in aqTemplates:
        items.insert(0, template)

    return items