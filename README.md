# hfmirror

[![PyPI](https://img.shields.io/pypi/v/hfmirror)](https://pypi.org/project/hfmirror/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/hfmirror)
![Loc](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/narugo1992/7eedd99825928ca780ec3aef60f7ce8d/raw/loc.json)
![Comments](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/narugo1992/7eedd99825928ca780ec3aef60f7ce8d/raw/comments.json)

[![Code Test](https://github.com/narugo1992/hfmirror/workflows/Code%20Test/badge.svg)](https://github.com/narugo1992/hfmirror/actions?query=workflow%3A%22Code+Test%22)
[![Package Release](https://github.com/narugo1992/hfmirror/workflows/Package%20Release/badge.svg)](https://github.com/narugo1992/hfmirror/actions?query=workflow%3A%22Package+Release%22)
[![codecov](https://codecov.io/gh/narugo1992/hfmirror/branch/main/graph/badge.svg?token=XJVDP4EFAT)](https://codecov.io/gh/narugo1992/hfmirror)

![GitHub Org's stars](https://img.shields.io/github/stars/narugo1992)
[![GitHub stars](https://img.shields.io/github/stars/narugo1992/hfmirror)](https://github.com/narugo1992/hfmirror/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/narugo1992/hfmirror)](https://github.com/narugo1992/hfmirror/network)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/narugo1992/hfmirror)
[![GitHub issues](https://img.shields.io/github/issues/narugo1992/hfmirror)](https://github.com/narugo1992/hfmirror/issues)
[![GitHub pulls](https://img.shields.io/github/issues-pr/narugo1992/hfmirror)](https://github.com/narugo1992/hfmirror/pulls)
[![Contributors](https://img.shields.io/github/contributors/narugo1992/hfmirror)](https://github.com/narugo1992/hfmirror/graphs/contributors)
[![GitHub license](https://img.shields.io/github/license/narugo1992/hfmirror)](https://github.com/narugo1992/hfmirror/blob/master/LICENSE)

Mirror for resources to local and huggingface.

## Installation

You can simply install it with `pip` command line from the official PyPI site.

```bash
pip install hfmirror
```

For more information about installation, you can refer to [Installation](https://narugo1992.github.io/hfmirror/main/tutorials/installation/index.html).

## Quick Start

### Mirror Github Releases to Your Disk

The following code can mirror the release files of repository `narugo1992/gchar` to your local directory `test_releases`

```python
from hfmirror.resource import GithubReleaseResource
from hfmirror.storage import LocalStorage
from hfmirror.sync import SyncTask

if __name__ == '__main__':
    github = GithubReleaseResource(
        # the github repository
        repo='narugo1992/gchar',

        # access_token of github client (if needed)
        access_token='my_github_access_token',

        # add files like LATEST_RELEASE to mark the versions
        add_version_attachment=True,
    )

    storage = LocalStorage('test_releases')

    task = SyncTask(github, storage)
    task.sync()

```

This is the `test_releases`

```
test_releases
├── LATEST_RELEASE
├── LATEST_RELEASE_0
├── LATEST_RELEASE_0.0
├── LATEST_RELEASE_0.0.1
├── LATEST_RELEASE_0.0.2
├── LATEST_RELEASE_0.0.3
├── LATEST_RELEASE_0.0.4
├── LATEST_RELEASE_0.0.5
├── LATEST_RELEASE_0.0.6
├── LATEST_RELEASE_0.0.8
├── v0.0.1
│   ├── gchar-0.0.1-py3-none-any.whl
│   └── gchar-0.0.1.tar.gz
├── v0.0.2
│   ├── gchar-0.0.2-py3-none-any.whl
│   └── gchar-0.0.2.tar.gz
├── v0.0.3
│   ├── gchar-0.0.3-py3-none-any.whl
│   └── gchar-0.0.3.tar.gz
├── v0.0.4
│   ├── gchar-0.0.4-py3-none-any.whl
│   └── gchar-0.0.4.tar.gz
├── v0.0.5
│   ├── gchar-0.0.5-py3-none-any.whl
│   └── gchar-0.0.5.tar.gz
├── v0.0.6
│   ├── gchar-0.0.6-py3-none-any.whl
│   └── gchar-0.0.6.tar.gz
└── v0.0.8
    ├── gchar-0.0.8-py3-none-any.whl
    └── gchar-0.0.8.tar.gz
```



### Mirror Game Skins to HuggingFace

Your can mirror the skins of genshin impact based on `gchar` to huggingface repo, using the following code with custom resource and huggingface repository storage:

```python
import mimetypes
import os
import re
from typing import Iterable, Union, Tuple, Any, Mapping, List, Type

from gchar.games.base import Character as BaseCharacter
from gchar.games.genshin import Character
from hbutils.system import urlsplit
from huggingface_hub import HfApi
from tqdm.auto import tqdm

from hfmirror.resource import SyncResource
from hfmirror.resource.resource import TargetPathType
from hfmirror.storage import HuggingfaceStorage
from hfmirror.sync import SyncTask
from hfmirror.utils import srequest, get_requests_session


class ArknightsSkinResource(SyncResource):
    def __init__(self, chs: List[Character], ch_type: Type[BaseCharacter]):
        self.characters = chs
        self.ch_type = ch_type
        self.session = get_requests_session()

    def grab(self) -> Iterable[Union[
        Tuple[str, Any, TargetPathType, Mapping],
        Tuple[str, Any, TargetPathType],
    ]]:
        yield 'metadata', {'game': self.ch_type.__game_name__}, ''
        _exist_ids = set()
        for ch in tqdm(self.characters):
            if ch.index in _exist_ids:
                continue

            metadata = {
                'id': ch.index,
                'cnname': str(ch.cnname) if ch.cnname else None,
                'jpname': str(ch.jpname) if ch.jpname else None,
                'enname': str(ch.enname) if ch.enname else None,
                'alias': list(map(str, ch.alias_names)),
            }
            yield 'metadata', metadata, f'{ch.index}'
            _exist_ids.add(ch.index)

            for skin in ch.skins:
                _, ext = os.path.splitext(urlsplit(skin.url).filename)
                if not ext:
                    resp = srequest(self.session, 'HEAD', skin.url)
                    ext = mimetypes.guess_extension(resp.headers['Content-Type'])

                filename = re.sub(r'\W+', '_', skin.name).strip('_') + ext
                yield 'remote', skin.url, f'{ch.index}/{filename}', {'name': skin.name}


if __name__ == '__main__':
    resource = ArknightsSkinResource(
        Character.all(contains_extra=False),
        Character
    )

    api = HfApi(token=os.environ['HF_TOKEN'])
    api.create_repo('narugo/test_repo', repo_type='dataset', exist_ok=True)
    storage = HuggingfaceStorage(
        repo='narugo/test_repo',
        hf_client=api,
        namespace='genshin',
    )

    task = SyncTask(resource, storage)
    task.sync()

```





