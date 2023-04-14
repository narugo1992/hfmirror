import re
import warnings
from typing import List, Iterable, Union, Mapping, Tuple, Any

from .resource import SyncResource
from ..utils import TargetPathType


def _to_int(v: Union[str, int]) -> Union[str, int]:
    try:
        return int(v)
    except (TypeError, ValueError):
        return v


class VersionBasedResource(SyncResource):
    def __init__(self, add_version_attachment: bool = True):
        SyncResource.__init__(self)
        self._versions = []
        self.register_operation('version', self._add_version)
        self.add_version_attachment = add_version_attachment

    def _add_version(self, version, segments: List[str], attached_data):
        _ = segments, attached_data
        self._versions.append(version)

    __version_pattern__ = r'^([a-zA-Z]+(\.|-)?)?(?P<version>[\d.]+)$'
    __version_file_prefix__ = 'LATEST_RELEASE'

    def _version_to_tuple(self, version):
        matching = re.fullmatch(self.__version_pattern__, version)
        if matching:
            version_text = matching.group('version')
            return tuple(map(_to_int, version_text.split('.')))
        else:
            raise ValueError(f'Invalid version for release - {version!r}.')

    def grab(self) -> Iterable[Union[
        Tuple[str, Any, TargetPathType, Mapping],
        Tuple[str, Any, TargetPathType],
    ]]:
        self._versions.clear()
        yield from self.grab_for_items()

        if self.add_version_attachment and self._versions:
            version_map = {}
            for version in self._versions:
                try:
                    _tuple = self._version_to_tuple(version)
                except ValueError:
                    warnings.warn(f'Version {version!r} does not match the regular expression, '
                                  f'so it will be ignored in version indexing.')
                    continue

                for i in range(len(_tuple) + 1):
                    _part_tuple = _tuple[:i]
                    if _part_tuple in version_map:
                        _exist_tuple, _exist_version = version_map[_part_tuple]
                        if _tuple > _exist_tuple:
                            version_map[_part_tuple] = (_tuple, version)
                    else:
                        version_map[_part_tuple] = (_tuple, version)

            for tuple_, (_, version) in version_map.items():
                if tuple_:
                    schema_file = f'{self.__version_file_prefix__}_{".".join(map(str, tuple_))}'
                else:
                    schema_file = self.__version_file_prefix__
                yield 'text', version, schema_file

    def grab_for_items(self) -> Iterable[Union[
        Tuple[str, Any, TargetPathType, Mapping],
        Tuple[str, Any, TargetPathType],
    ]]:
        raise NotImplementedError  # pragma: no cover
