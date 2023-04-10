import re
from typing import Tuple, Optional, Mapping, Any, Union, Iterable

from github import Github
from github.GitRelease import GitRelease
from tqdm.auto import tqdm

from .resource import SyncResource, TargetPathType


def _to_int(v: Union[str, int]) -> Union[str, int]:
    try:
        return int(v)
    except (TypeError, ValueError):
        return v


class GithubReleaseResource(SyncResource):
    def __init__(self, repo: str, access_token: Optional[str] = None, add_version_attachment: bool = True):
        self.repo = repo
        self.github_client = Github(access_token)
        self.add_version_attachment = add_version_attachment

    def _tag_filter(self, tag):
        return tag

    def _filename_filter(self, tag, filename):
        _ = tag
        return filename

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
        repo = self.github_client.get_repo(self.repo)
        versions = []
        repo_tqdm = tqdm(repo.get_releases())
        for release in repo_tqdm:
            release: GitRelease
            tag_name = self._tag_filter(release.tag_name)
            repo_tqdm.set_description(tag_name)
            if not tag_name:
                continue

            versions.append(tag_name)
            yield 'metadata', {'version': release.tag_name}, tag_name
            for asset in release.get_assets():
                filename = self._filename_filter(tag_name, asset.name)
                if not filename:
                    continue

                download_url = asset.browser_download_url
                metadata = {'tag': release.tag_name, 'filename': asset.name}
                yield 'remote', download_url, f'{tag_name}/{filename}', metadata

        if self.add_version_attachment:
            version_map = {}
            for version in versions:
                _tuple = self._version_to_tuple(version)
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
