import os
import re
from typing import List, Union

TargetPathType = Union[str, List[str]]

_FORBIDDEN_CHARS = {'<', '>', ':', '\"', '/', '\\', '|', '?', '*', *(chr(ich) for ich in range(1, 32))}
_FORBIDDEN_SEGMENTS = [
    'CON', 'PRN', 'AUX', 'NUL',
    'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
    'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9',
]


def to_segments(path: TargetPathType) -> List[str]:
    if isinstance(path, (list, tuple)):
        segments = map(str, path)
    else:
        segments = re.split(r'[\\/]+', path)
    segments = list(filter(bool, segments))

    for i, segment in enumerate(segments):
        for ch in segment:
            if ch in _FORBIDDEN_CHARS:
                raise ValueError(f'Segment #{i} contains invalid character - {segment!r}.')

        for fseg in _FORBIDDEN_SEGMENTS:
            if fseg.lower() == segment.lower():
                raise ValueError(f'Segment #{i} is preserved - {segment!r}.')

    normed_path = os.path.relpath(os.path.normpath(os.path.join(os.path.sep, *segments)), start=os.path.sep)
    segments = normed_path.split(os.path.sep)
    return [] if segments == ['.'] else segments
