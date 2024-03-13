from .utils import sync_folder

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..processor import AquariumProcessor

def created(processor: "AquariumProcessor", event):
    sync_folder(processor, event)

def updated(processor: "AquariumProcessor", event):
    sync_folder(processor, event)

