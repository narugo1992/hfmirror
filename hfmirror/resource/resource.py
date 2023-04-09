import io
import os
import re
import warnings
from operator import itemgetter
from typing import Tuple, List, Mapping, Any, Iterable, Union, Dict

from hbutils.string.tree import format_tree

from .item import create_sync_item, SyncItem, _PRESERVED_NAMES

_TargetPathType = Union[str, List[str]]


def _split_path_to_segments(path: _TargetPathType) -> List[str]:
    if isinstance(path, (list, tuple)):
        return list(path)
    else:
        return list(filter(bool, re.split(r'[\\/]+', path)))


def _prefix_fix(text: str, prefix: str) -> str:
    prefix_lines = prefix.splitlines(keepends=False)
    max_prefix_length = max(map(len, prefix_lines))

    text_lines = text.splitlines(keepends=False)
    if len(text_lines) < len(prefix_lines):
        text_lines += [''] * (len(prefix_lines) - len(text_lines))
    if len(prefix_lines) < len(text_lines):
        prefix_lines += [''] * (len(text_lines) - len(prefix_lines))

    lines = []
    for i, (prefix_line, text_line) in enumerate(zip(prefix_lines, text_lines)):
        if text_line and len(prefix_line) < max_prefix_length:
            prefix_line = prefix_line + ' ' * (max_prefix_length - len(prefix_line))
        lines.append(prefix_line + text_line)

    return os.linesep.join(lines)


class MetadataItem:
    def __init__(self, data: Mapping, segments: List[str]):
        self.data = data
        self.segments = segments

    def __repr__(self):
        return f'<{self.__class__.__name__} data: {self.data!r}>'


def _metadata_repr(metadata: Mapping):
    with io.StringIO() as f:
        for key in sorted(metadata.keys()):
            print(f'{key}: {metadata[key]!r}', file=f)

        return f.getvalue()


def _text_concat(*texts):
    lines = []
    for text in texts:
        lines.extend(text.splitlines(keepends=False))

    return os.linesep.join(lines)


class SyncTree:
    def __init__(self):
        self.metadata: dict = {}
        self.items: Dict[str, Union[SyncItem, SyncTree]] = {}

    def _add_item_with_segment(self, item: SyncItem, segments: List[str]):
        current = segments[0]
        if len(segments) > 1:  # still a path
            if current not in self.items or isinstance(self.items[current], SyncTree):
                if current not in self.items:
                    self.items[current] = SyncTree()
                self.items[current]._add_item_with_segment(item, segments[1:])
            elif isinstance(self.items[current], SyncItem):
                raise TypeError(f'Sync item ({"/".join(segments)}) is an item, '
                                f'unable to be set a child item ({item!r}) for it.')
            else:
                assert False, 'Unable to reach here #1, ' \
                              'please open an issue to let the author know.'  # pragma: no cover

        else:  # is a file
            if current not in self.items:
                self.items[current] = item
            elif isinstance(self.items[current], SyncItem):
                warnings.warn(f'Sync item ({self.items[current]!r}) at {"/".join(segments)} '
                              f'will be replaced by {item!r}.')
                self.items[current] = item
            elif isinstance(self.items[current], SyncTree):
                raise TypeError(f'Sync position ({"/".join(segments)}) is a folder, '
                                f'unable to be replace with item {item!r}.')
            else:
                assert False, 'Unable to reach here #2, ' \
                              'please open an issue to let the author know.'  # pragma: no cover

    def add_item(self, item: SyncItem):
        self._add_item_with_segment(item, item.segments)

    def _add_meta_item_with_segment(self, item: MetadataItem, segments: List[str]):
        if not segments:
            self.metadata.update(**item.data)
        else:
            current = segments[0]
            if current not in self.items:
                self.items[current] = SyncTree()

            if isinstance(self.items[current], SyncItem):
                if len(segments) == 1:
                    self.items[current].metadata.update(**item.data)
                else:
                    raise TypeError(f'Unable to set metadata {item.data!r} with position {"/".join(segments)} to '
                                    f'the child position of an item {"/".join(self.items[current].segments)}.')
            elif isinstance(self.items[current], SyncTree):
                self.items[current]._add_meta_item_with_segment(item, segments[1:])
            else:
                assert False, 'Unable to reach here #3, ' \
                              'please open an issue to let the author know.'  # pragma: no cover

    def add_meta_item(self, item: MetadataItem):
        self._add_meta_item_with_segment(item, item.segments)

    def _data_for_repr(self):
        def _recursion(tree, path):
            if isinstance(tree, SyncTree):
                label = _text_concat(path, '[Metadata]', _metadata_repr(tree.metadata)) if tree.metadata else path
                return label, [
                    _recursion(tree.items[key], key)
                    for key in sorted(tree.items.keys())
                ]
            else:
                body = _text_concat(repr(tree), '[Metadata]', _metadata_repr(tree.metadata)) \
                    if tree.metadata else repr(tree)
                return _prefix_fix(body, f'{path} --> '), []

        return _recursion(self, '<root>')

    def __repr__(self):
        return format_tree(self._data_for_repr(), itemgetter(0), itemgetter(1))


SyncItemType = Union[SyncItem, MetadataItem]


class SyncResource:
    def grab(self) -> Iterable[Union[
        Tuple[str, Any, _TargetPathType, Mapping],
        Tuple[str, Any, _TargetPathType],
    ]]:
        raise NotImplementedError

    def iter_sync_items(self) -> Iterable[SyncItemType]:
        for tpl in self.grab():
            if isinstance(tpl, tuple):
                if len(tpl) == 3:
                    (type_, value, path), attached_data = tpl, {}
                elif len(tpl) == 4:
                    type_, value, path, attached_data = tpl
                else:
                    raise ValueError(f'Sync type data should be a tuple '
                                     f'with length 3 or 4, but {tpl!r} found.')

                segments = _split_path_to_segments(path)
                if type_ in _PRESERVED_NAMES:
                    if type_ == 'metadata':
                        if attached_data:
                            warnings.warn(f'Attached data {attached_data!r} for position {tpl!r} '
                                          f'will be ignored when defining metadata.')
                        yield MetadataItem(value, segments)

                    else:
                        assert False, f'Undefined preserved operation - {type_!r}, ' \
                                      f'please notice the author about this.'
                else:
                    yield create_sync_item(type_, value, attached_data, segments)

            else:
                raise TypeError(f'Invalid sync type data - {tpl!r}.')

    def sync_tree(self) -> SyncTree:
        tree = SyncTree()
        meta_items: List[MetadataItem] = []
        for item in self.iter_sync_items():
            if isinstance(item, MetadataItem):
                meta_items.append(item)
            else:
                tree.add_item(item)

        for item in meta_items:
            tree.add_meta_item(item)

        return tree
