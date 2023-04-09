import os.path
import pathlib
import shutil
from contextlib import contextmanager
from typing import List, Optional, Tuple

from hbutils.system.filesystem.tempfile import TemporaryDirectory

from .base import BaseStorage


class LocalStorage(BaseStorage):
    def __init__(self, root_directory, namespace: List[str] = None):
        self.root_directory = root_directory
        self.namespace = list(namespace or [])

    def path_join(self, path, *segments):
        return os.path.join(self.root_directory, *self.namespace, path, *segments)

    def file_exists(self, file: List[str]) -> bool:
        file = self.path_join(*file)
        return os.path.exists(file) and os.path.isfile(file)

    def read_text(self, file: List[str]) -> str:
        file = self.path_join(*file)
        return pathlib.Path(file).read_text()

    @contextmanager
    def recover_state_when_failed(self, state: List[List[str]]):
        with TemporaryDirectory() as td:
            # record all the files
            records = []
            for i, file_in_storage in enumerate(state):
                file_in_storage = self.path_join(*file_in_storage)
                if os.path.exists(file_in_storage):
                    file_in_temp = os.path.join(td, f'{i}', os.path.basename(file_in_storage))
                    os.makedirs(os.path.join(td, f'{i}'), exist_ok=True)
                    shutil.copyfile(file_in_storage, file_in_temp)
                    records.append(file_in_temp)
                else:
                    records.append(None)

            try:
                yield
            except:
                # recover all the files
                for file_in_temp, file_in_storage in zip(records, state):
                    file_in_storage = self.path_join(*file_in_storage)
                    if file_in_temp is None:
                        if os.path.exists(file_in_storage):
                            os.remove(file_in_storage)
                    else:
                        directory = os.path.dirname(file_in_storage)
                        if directory:
                            os.makedirs(directory, exist_ok=True)
                        shutil.copyfile(file_in_temp, file_in_storage)

                raise

    def batch_change_files(self, changes: List[Tuple[Optional[str], List[str]]]):
        states = [file_in_storage for _, file_in_storage in changes]
        with self.recover_state_when_failed(states):
            for local_file, file_in_storage in changes:
                file_in_storage = self.path_join(*file_in_storage)
                if local_file is None:
                    if os.path.exists(file_in_storage):
                        os.remove(file_in_storage)
                else:
                    directory = os.path.dirname(file_in_storage)
                    if directory:
                        os.makedirs(directory, exist_ok=True)
                    shutil.copyfile(local_file, file_in_storage)
