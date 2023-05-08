import warnings
from typing import Tuple, Mapping, Any, Union, Iterable, Optional

from github import Github
from github.GitRelease import GitRelease
from tqdm.auto import tqdm

from .resource import TargetPathType
from .version import VersionBasedResource


def _to_int(v: Union[str, int]) -> Union[str, int]:
    try:
        return int(v)
    except (TypeError, ValueError):
        return v


class GithubReleaseResource(VersionBasedResource):
    def __init__(self, repo: str, *,
                 github_client: Optional[Github] = None,
                 access_token: Optional[str] = None,
                 add_version_attachment: bool = True):
        VersionBasedResource.__init__(self, add_version_attachment)
        self.repo = repo
        if github_client and access_token:
            warnings.warn('Github client provided, so access token will be ignored.', stacklevel=2)
        self.github_client = github_client or Github(access_token)

    def _tag_filter(self, tag):
        return tag

    def _filename_filter(self, tag, filename):
        _ = tag
        return filename

    def grab_for_items(self) -> Iterable[Union[
        Tuple[str, Any, TargetPathType, Mapping],
        Tuple[str, Any, TargetPathType],
    ]]:
        repo = self.github_client.get_repo(self.repo)
        yield 'metadata', {'source': repo.html_url}, ''
        repo_tqdm = tqdm(repo.get_releases())
        for release in repo_tqdm:
            release: GitRelease
            tag_name = self._tag_filter(release.tag_name)
            repo_tqdm.set_description(tag_name)
            if not tag_name:
                continue

            has_file = False
            for asset in release.get_assets():
                filename = self._filename_filter(tag_name, asset.name)
                if not filename:
                    continue

                download_url = asset.browser_download_url
                metadata = {'tag': release.tag_name, 'filename': asset.name}
                yield 'remote', download_url, f'{tag_name}/{filename}', metadata
                has_file = True

            if has_file:
                yield 'version', tag_name, tag_name
                release_metadata = {'version': release.tag_name, 'title': release.title, 'url': release.html_url}
                yield 'metadata', release_metadata, tag_name
