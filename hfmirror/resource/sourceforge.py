import re
from cgi import parse_header
from typing import Iterable, Tuple, Optional, List
from typing import Union, Any, Mapping
from urllib import parse as urlparse
from urllib.parse import urljoin, quote

from pyquery import PyQuery as pq
from tqdm.auto import tqdm

from .item import RemoteSyncItem, register_sync_type
from .version import VersionBasedResource
from ..utils import TargetPathType, srequest, get_requests_session, to_segments


def _iterdir_on_sourceforge(url, segments, session=None) -> Iterable[Tuple[str, str, str]]:
    session = session or get_requests_session()
    resp = srequest(session, 'GET', url)

    list_tqdm = tqdm(list(pq(resp.text)('#files_list tbody > tr').items()))
    for row in list_tqdm:
        th = row('th:nth-child(1)')
        name = th('.name').text().strip()
        list_tqdm.set_description('/'.join([*segments, name]))
        download_page_url = urljoin(resp.url, th('a').attr('href'))
        type_, = re.findall(r'(download|enter)', th('a').attr('title'))
        if type_ == 'download':
            r = srequest(session, 'GET', download_page_url)
            raw_download_url = None
            for item in parse_header(pq(r.text)('noscript meta').attr('content')):
                if isinstance(item, dict) and 'url' in item:
                    raw_download_url = item['url']
                    break

            assert raw_download_url, f'Raw download url not found on {download_page_url!r}.'
            download_url = urlparse.urlunsplit(urlparse.urlsplit(raw_download_url)._replace(query=''))
            yield 'file', name, download_url
        else:
            yield 'directory', name, download_page_url


class WgetRemoteItem(RemoteSyncItem):
    __type__ = 'wget'
    __headers__ = {'User-Agent': 'Wget/1.20.3 (linux-gnu)'}


register_sync_type(WgetRemoteItem)


class SourceForgeFilesResource(VersionBasedResource):
    def __init__(self, project_name, subdir='', add_version_attachment: bool = True):
        VersionBasedResource.__init__(self, add_version_attachment)
        self.project_name = project_name
        self.subdir = to_segments(subdir)
        self.root_url = f"https://sourceforge.net/projects/" \
                        f"{quote(project_name)}/files/{'/'.join(map(quote, self.subdir))}"

    def _process_segments(self, type_, segments) -> Optional[List[str]]:
        _ = type_, segments
        return segments

    def _get_version(self, type_, segments) -> Optional[str]:
        _ = type_, segments
        return None

    def _walk_on_sourceforge(self, url, segments, session=None):
        session = session or get_requests_session()
        for type_, name, download_url in _iterdir_on_sourceforge(url, segments, session):
            current_segments = [*segments, name]
            _to_segments = self._process_segments(type_, current_segments)
            if _to_segments is not None:
                yield type_, _to_segments, download_url
                if type_ == 'directory':
                    yield from self._walk_on_sourceforge(download_url, current_segments, session)

    def grab_for_items(self) -> Iterable[Union[
        Tuple[str, Any, TargetPathType, Mapping],
        Tuple[str, Any, TargetPathType],
    ]]:
        yield 'metadata', {'source': self.root_url}, ''
        session = get_requests_session()
        for type_, segments, download_url in self._walk_on_sourceforge(self.root_url, [], session):
            if type_ == 'file':
                yield 'wget', download_url, segments
            else:  # directory
                yield 'metadata', {'page_url': download_url}, segments

            version = self._get_version(type_, segments)
            if version is not None:
                yield 'version', version, segments
