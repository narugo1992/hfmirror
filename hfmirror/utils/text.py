import os
from dataclasses import dataclass
from typing import Union


def text_concat(*texts):
    lines = []
    for text in texts:
        lines.extend(text.splitlines(keepends=False))
    return os.linesep.join(lines)


class _TextBlock:
    def __init__(self, text: str, keepends: bool = False, pad: bool = True):
        self._lines = text.splitlines(keepends=keepends)
        self._max_width = max(map(len, self._lines))
        self._pad = pad

    def _pad_line(self, line):
        if self._pad:
            return line + ' ' * (self._max_width - len(line))
        else:
            return line

    def __getitem__(self, item: int):
        if isinstance(item, int):
            if item >= len(self._lines):
                line = ''
            else:
                line = self._lines[item]

            return self._pad_line(line)
        else:
            raise TypeError(f'Supported item type - {item!r}.')  # pragma: no cover

    def __len__(self):
        return len(self._lines)


class _CycleTextBlock(_TextBlock):
    def __getitem__(self, item: int):
        return _TextBlock.__getitem__(self, item % len(self))


@dataclass
class _CycleTextBlockProxy:
    text: str


def _to_text_block(x, **kwargs) -> _TextBlock:
    if isinstance(x, _CycleTextBlockProxy):
        return _CycleTextBlock(x.text, **kwargs)
    elif isinstance(x, str):
        return _TextBlock(x, **kwargs)
    else:
        raise TypeError(f'Unknown type of text block - {x!r}.')


def cycle(text):
    return _CycleTextBlockProxy(text)


def text_parallel(*texts: Union[str, _CycleTextBlockProxy]):
    if not texts:
        return ''

    blocks = [_to_text_block(x, pad=i < (len(texts) - 1)) for i, x in enumerate(texts)]
    native_blocks = [x for x in blocks if not isinstance(x, _CycleTextBlock)]
    max_lines = max(map(len, native_blocks))

    lines = []
    for i in range(max_lines):
        parts = [b[i] for b in blocks]
        lines.append(''.join(parts))

    return os.linesep.join(lines)
