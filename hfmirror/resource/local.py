import os
from typing import Iterable, Union, Tuple, Any, Mapping

from .resource import SyncResource
from ..utils import TargetPathType


class LocalDirectoryResource(SyncResource):
    def __init__(self, directory):
        SyncResource.__init__(self)
        self.directory = directory

    def grab(self) -> Iterable[Union[
        Tuple[str, Any, TargetPathType, Mapping],
        Tuple[str, Any, TargetPathType],
    ]]:
        for root, dirs, files in os.walk(self.directory):
            for file in files:
                path = os.path.abspath(os.path.join(root, file))
                relpath = os.path.relpath(path, self.directory)
                yield 'local', path, relpath
