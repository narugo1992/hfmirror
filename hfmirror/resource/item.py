import os.path
import tempfile
from contextlib import contextmanager
from email.utils import parsedate_to_datetime
from typing import List, Mapping, ContextManager, Optional

from hbutils.string import truncate
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
    def __init__(self, gene, data, segments):
        SyncItem.__init__(self, data, segments)
        self.gene = gene

    @contextmanager
    def load_file(self) -> ContextManager[str]:
        with self.gene() as f:
            yield f

    def __repr__(self):
        return f'<{self.__class__.__name__} gene: {self.gene!r}>'


class ContentOutputItem(SyncItem):
    def __init__(self, content, data, segments):
        SyncItem.__init__(self, data, segments)
        self.content = content

    @contextmanager
    def load_file(self) -> ContextManager[str]:
        with tempfile.TemporaryDirectory() as td:
            filename = os.path.join(td, 'file')
            with open(filename, 'w') as f:
                f.write(self.content)

            yield filename

    def __repr__(self):
        return f'<{self.__class__.__name__} content: {truncate(self.content, tail_length=15, show_length=True)!r}>'
