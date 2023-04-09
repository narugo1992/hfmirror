import os.path
import re
import tempfile
from contextlib import contextmanager
from email.utils import parsedate_to_datetime
from typing import Tuple, List, Mapping, Any, ContextManager, Optional

from hbutils.system.network import urlsplit

from ..utils import file_download, srequest, get_requests_session


class SyncItem:
    def __init__(self, data: Mapping, segments: List[str]):
        self.data = data
        self.segments = segments

    def load_file(self) -> ContextManager[str]:
        raise NotImplementedError


class ResourceNotChange(Exception):
    pass


class RemoteSyncItem(SyncItem):
    __order__ = 0

    def __init__(self, url, data, segments: List[str]):
        SyncItem.__init__(self, data, segments)
        self.url = url

    def _file_process(self, filename):
        pass

    @contextmanager
    def load_file(self) -> ContextManager[str]:
        with tempfile.TemporaryDirectory() as td:
            filename = os.path.join(td, urlsplit(self.url).filename or 'unnamed_file')
            file_download(self.url, filename)
            self._file_process(filename)
            yield filename

    def get_etag(self, etag: Optional[str] = None):
        session = get_requests_session()
        resp = srequest(session, 'HEAD', self.url, allow_redirects=True, headers={'If-Not-Match': etag} if etag else {})
        if resp.status_code == 304:
            raise ResourceNotChange
        else:
            headers = resp.headers
            etag = headers.get('ETag')
            expires = headers.get('Expires')
            expires = parsedate_to_datetime(expires).timestamp() if expires else None
            date = headers.get('Date')
            date = parsedate_to_datetime(date).timestamp() if date else None
            content_length = headers.get('Content-Length')
            content_length = int(content_length) if content_length is not None else None
            content_type = headers.get('Content-Type')

            return {
                'url': self.url,
                'etag': etag,
                'expires': expires,
                'date': date,
                'content_length': content_length,
                'content_type': content_type,
            }

    def __repr__(self):
        return f'<{self.__class__.__name__} url: {self.url!r}>'


class CustomSyncItem(SyncItem):
    __order__ = 1

    def __init__(self, gene, data, segments):
        SyncItem.__init__(self, data, segments)
        self.gene = gene

    @contextmanager
    def load_file(self) -> ContextManager[str]:
        with self.gene() as f:
            yield f

    def __repr__(self):
        return f'<{self.__class__.__name__} gene: {self.gene!r}>'


class SyncResource:
    def sync(self) -> Tuple[List[Tuple[str, str, Mapping]], Mapping]:
        raise NotImplementedError

    def custom(self, metadata) -> List[Tuple[Any, str, Mapping]]:
        _ = metadata
        return []

    def items(self) -> List[SyncItem]:
        items: List[SyncItem] = []
        pairs, metadata = self.sync()
        for url, path, data in pairs:
            path_segments = list(filter(bool, re.split(r'[\\/]+', path)))
            if not path_segments:
                raise ValueError(f'Invalid path with no segments - {path!r}.')
            items.append(RemoteSyncItem(url, data, path_segments))

        for gene, path, data in self.custom(metadata):
            path_segments = list(filter(bool, re.split(r'[\\/]+', path)))
            if not path_segments:
                raise ValueError(f'Invalid path with no segments - {path!r}.')
            items.append(CustomSyncItem(gene, data, path_segments))

        retval = []
        for _, item in sorted(enumerate(items), key=lambda x: (-len(x[1].segments), x[1].segments, x[0])):
            retval.append(item)

        return retval
