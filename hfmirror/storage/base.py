from typing import List, Optional, Tuple


class BaseStorage:
    def path_join(self, path, *segments):
        raise NotImplementedError  # pragma: no cover

    def file_exists(self, file: List[str]) -> bool:
        raise NotImplementedError  # pragma: no cover

    def read_text(self, file: List[str], encoding: str = 'utf-8') -> str:
        raise NotImplementedError  # pragma: no cover

    def batch_change_files(self, changes: List[Tuple[Optional[str], List[str]]]):
        raise NotImplementedError  # pragma: no cover
