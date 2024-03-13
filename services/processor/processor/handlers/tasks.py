from .utils import sync_task

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..processor import AquariumProcessor

def created(processor: "AquariumProcessor", event):
    sync_task(processor, event)

def updated(processor: "AquariumProcessor", event):
    sync_task(processor, event)

def assigned(processor: "AquariumProcessor", event):
    sync_task(processor, event)