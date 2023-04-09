from typing import List, Optional


class BaseStorage:
    def path_join(self, path, *segments):
        raise NotImplementedError

    def file_exists(self, file: List[str]) -> bool:
        raise NotImplementedError

    def read_text(self, file: List[str]) -> str:
        raise NotImplementedError

    def batch_change_files(self, changes: List[Optional[str], List[str]]):
        raise NotImplementedError
