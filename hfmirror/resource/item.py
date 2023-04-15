import abc
import os.path
import time
from contextlib import contextmanager
from email.utils import parsedate_to_datetime
from typing import List, ContextManager, Optional, Type, Any, Dict

import requests
from hbutils.string import truncate
from hbutils.system.filesystem.tempfile import TemporaryDirectory
from hbutils.system.network import urlsplit

from ..utils import download_file, srequest, get_requests_session, hash_anything


class ResourceNotChange(Exception):
    pass


class SyncItem(metaclass=abc.ABCMeta):
    __type__: str = None

    def __init__(self, value, metadata: dict, segments: List[str]):
        self._value = value
        self.metadata = metadata
        self.segments = segments

    def load_file(self) -> ContextManager[str]:
        raise NotImplementedError  # pragma: no cover

    def refresh_mark(self, mark: Optional[Dict[str, Any]]):
        return mark or {}

    def __hash__(self):
        return hash_anything((type(self), self._value, self.metadata, self.segments))

    def __eq__(self, other):
        if self is other:
            return True
        elif isinstance(self, type(other)) and isinstance(other, type(self)):
            return (self._value, self.metadata, self.segments) == \
                (other._value, other.metadata, other.segments)
        else:
            return False


class RemoteSyncItem(SyncItem):
    __type__ = 'remote'
    __headers__ = {}
    __request_kwargs__ = {}

    def __init__(self, url, metadata, segments: List[str]):
        SyncItem.__init__(self, url, metadata, segments)
        self.url = url
        self._session = None

    def get_new_session(self):
        return get_requests_session(headers=self.__headers__)

    def _get_session(self) -> requests.Session:
        if self._session is None:
            self._session = self.get_new_session()

        return self._session

    def _file_process(self, filename):
        pass

    @contextmanager
    def load_file(self) -> ContextManager[str]:
        with TemporaryDirectory() as td:
            filename = os.path.join(td, urlsplit(self.url).filename or 'unnamed_file')
            download_file(self.url, filename, session=self._get_session(), **self.__request_kwargs__)
            self._file_process(filename)
            yield filename

    def refresh_mark(self, mark: Optional[Dict[str, Any]]):
        mark = dict(mark or {})
        url = mark.get('url')
        if url == self.url:  # url not changed
            expires = mark.get('expires')
            if expires is not None and time.time() < expires:
                raise ResourceNotChange

            etag = mark.get('etag')
            headers = {'If-None-Match': etag} if etag else {}
        else:
            headers = {}

        kwargs = self.__request_kwargs__.copy()
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
            kwargs.pop('headers')

        resp = srequest(
            self._get_session(), 'HEAD', self.url,
            allow_redirects=True, headers=headers,
            **kwargs
        )
        if resp.status_code == 304:
            raise ResourceNotChange

        headers = resp.headers
        etag = headers.get('ETag')
        expires = headers.get('Expires')
        expires = parsedate_to_datetime(expires).timestamp() if expires else None
        content_length = headers.get('Content-Length')
        content_length = int(content_length) if content_length is not None else None
        content_type = headers.get('Content-Type')

        return {
            'url': self.url,
            'etag': etag,
            'expires': expires,
            'content_length': content_length,
            'content_type': content_type,
        }

    def __repr__(self):
        return f'<{self.__class__.__name__} url: {self.url!r}>'


class CustomSyncItem(SyncItem):
    __type__ = 'custom'

    def __init__(self, gene, metadata, segments):
        SyncItem.__init__(self, gene, metadata, segments)
        self.gene = gene

    @contextmanager
    def load_file(self) -> ContextManager[str]:
        with self.gene() as f:
            yield f

    def __repr__(self):
        return f'<{self.__class__.__name__} gene: {self.gene!r}>'


class TextOutputSyncItem(SyncItem):
    __type__ = 'text'

    def __init__(self, content, metadata, segments):
        SyncItem.__init__(self, content, metadata, segments)
        self.content = content

    @contextmanager
    def load_file(self) -> ContextManager[str]:
        with TemporaryDirectory() as td:
            filename = os.path.join(td, 'file')
            with open(filename, 'w') as f:
                f.write(self.content)

            yield filename

    def __repr__(self):
        return f'<{self.__class__.__name__} content: {truncate(self.content, tail_length=15, show_length=True)!r}>'


_PRESERVED_NAMES = {'metadata'}
_REGISTERED_SYNC_TYPES: Dict[str, Type[SyncItem]] = {}


def register_sync_type(clazz: Type[SyncItem]):
    type_ = clazz.__type__
    if type_ is None:
        raise TypeError(f'Sync item class {clazz!r} should have __type__ instead of None.')
    elif type_ in _PRESERVED_NAMES:
        raise KeyError(f'Type {type_!r} is preserved, please use another one.')
    elif type_ in _REGISTERED_SYNC_TYPES:
        raise KeyError(f'Sync item type {type_!r} already exist.')
    else:
        _REGISTERED_SYNC_TYPES[type_] = clazz


register_sync_type(RemoteSyncItem)
register_sync_type(CustomSyncItem)
register_sync_type(TextOutputSyncItem)


def create_sync_item(type_: str, value: Any, metadata: dict, segments: List[str]) -> SyncItem:
    if type_ in _REGISTERED_SYNC_TYPES:
        clazz = _REGISTERED_SYNC_TYPES[type_]
        return clazz(value, metadata, segments)
    else:
        raise KeyError(f'Unknown sync item type - {type_!r}.')
