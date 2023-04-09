from typing import List, Optional, Tuple


class BaseStorage:
    def path_join(self, path, *segments):
        raise NotImplementedError

    def file_exists(self, file: List[str]) -> bool:
        raise NotImplementedError

    def read_text(self, file: List[str]) -> str:
        raise NotImplementedError

    def batch_change_files(self, changes: List[Tuple[Optional[str], List[str]]]):
        raise NotImplementedError
