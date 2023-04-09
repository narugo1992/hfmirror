from ..resource import SyncResource
from ..storage import BaseStorage


class SyncTask:
    __meta_filename__ = '.meta.json'

    def __init__(self, resource: SyncResource, storage: BaseStorage):
        self.resource = resource
        self.storage = storage

    def sync(self):
        pass
