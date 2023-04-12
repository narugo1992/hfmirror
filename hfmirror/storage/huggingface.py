import datetime
import os
import warnings
from hashlib import sha256, sha1
from typing import List, Tuple, Optional, Union

import requests
from huggingface_hub import HfApi, hf_hub_url, CommitOperationAdd, CommitOperationDelete

from .base import BaseStorage
from ..utils import to_segments, srequest, get_requests_session


def hf_resource_check(local_filename, repo_id: str, file_in_repo: str, repo_type='dataset', revision='main',
                      chunk_for_hash: int = 1 << 20):
    response = requests.post(
        f"https://huggingface.co/api/{repo_type}s/{repo_id}/paths-info/{revision}",
        json={"paths": [file_in_repo]},
    )
    _raw_data = response.json()
    if not _raw_data:
        return False

    metadata = response.json()[0]
    if 'lfs' in metadata:
        is_lfs, oid, filesize = True, metadata['lfs']['oid'], metadata['lfs']['size']
    else:
        is_lfs, oid, filesize = False, metadata['oid'], metadata['size']

    if filesize != os.path.getsize(local_filename):
        return False

    if is_lfs:
        sha = sha256()
    else:
        sha = sha1()
        sha.update(f'blob {filesize}\0'.encode('utf-8'))
    with open(local_filename, 'rb') as f:
        # make sure the big files will not cause OOM
        while True:
            data = f.read(chunk_for_hash)
            if not data:
                break
            sha.update(data)

    return sha.hexdigest() == oid


def _check_repo_type(repo_type):
    if repo_type in {'model', 'dataset', 'space'}:
        return repo_type
    else:
        raise ValueError(f'Invalid huggingface repository type - {repo_type!r}.')


class HuggingfaceStorage(BaseStorage):
    def __init__(self, repo: str, repo_type: str = 'dataset', revision: str = 'main',
                 hf_client: Optional[HfApi] = None, access_token: Optional[str] = None,
                 namespace: Union[List[str], str, None] = None):
        if hf_client and access_token:
            warnings.warn('Huggingface client provided, so access token will be ignored.', stacklevel=2)
        self.hf_client = hf_client or HfApi(token=access_token)
        self.repo = repo
        self.repo_type = repo_type
        self.revision = revision
        self.namespace = to_segments(namespace or [])
        self.session = get_requests_session()

    def path_join(self, path, *segments):
        return '/'.join((*self.namespace, path, *segments))

    def _file_url(self, file: List[str]):
        return hf_hub_url(self.repo, self.path_join(*file), repo_type=self.repo_type, revision=self.revision)

    def file_exists(self, file: List[str]) -> bool:
        resp = srequest(self.session, 'HEAD', self._file_url(file), raise_for_status=False)
        return resp.ok

    def read_text(self, file: List[str], encoding: str = 'utf-8') -> str:
        return srequest(self.session, 'GET', self._file_url(file)).content.decode(encoding=encoding)

    def batch_change_files(self, changes: List[Tuple[Optional[str], List[str]]]):
        operations = []
        ops = []
        for local_filename, file_in_repo in changes:
            fip = self.path_join(*file_in_repo)
            if local_filename is None:
                operations.append(CommitOperationDelete(path_in_repo=fip))
                ops.append(f'-{fip}')
            else:
                if not hf_resource_check(
                        local_filename, self.repo,
                        file_in_repo=fip,
                        repo_type=self.repo_type,
                        revision=self.revision,
                ):
                    operations.append(CommitOperationAdd(
                        path_in_repo=fip,
                        path_or_fileobj=local_filename
                    ))
                    ops.append(f'+{fip}')

        if operations:
            current_time = datetime.datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')
            msg = ', '.join(ops)
            self.hf_client.create_commit(
                self.repo, operations,
                commit_message=f"{msg}, on {current_time}",
                repo_type=self.repo_type,
                revision=self.revision,
            )
