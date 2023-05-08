import datetime
import os
import warnings
from functools import partial, lru_cache
from hashlib import sha256, sha1
from typing import List, Tuple, Optional, Union, Dict

from huggingface_hub import HfApi, hf_hub_url, CommitOperationAdd, CommitOperationDelete, configure_http_backend

from .base import BaseStorage
from ..utils import to_segments, srequest, get_requests_session

DEFAULT_TIMEOUT: int = 10


@lru_cache()
def _register_session_for_hf(max_retries: int = 5, timeout: int = DEFAULT_TIMEOUT,
                             headers: Optional[Dict[str, str]] = None):
    configure_http_backend(backend_factory=partial(get_requests_session, max_retries, timeout, headers))


def _single_resource_is_duplicated(local_filename: str, is_lfs: bool, oid: str, filesize: int,
                                   chunk_for_hash: int = 1 << 20) -> bool:
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


def hf_local_upload_check(uploads: List[Tuple[Optional[str], str]],
                          repo_id: str, repo_type='dataset', revision='main',
                          chunk_for_hash: int = 1 << 20, session=None) -> List[Tuple[bool, str]]:
    """
    Overview:
        Check resource on huggingface repo and local.

    :param uploads: Tuples of uploads, the first item is the local file, second item is the file in repo. When \
        first item is None, it means delete this item in repo.
    :param repo_id: Repository id, the same as that in huggingface library.
    :param repo_type: Repository type, the same as that in huggingface library.
    :param revision: Revision of repository, the same as that in huggingface library.
    :param chunk_for_hash: Chunk size for hashing calculation.
    :param session: Session of requests, will be auto created when not given.
    :return: Uploads are necessary or not, in form of lists of boolean.
    """
    if not uploads:
        return []

    session = session or get_requests_session()
    files_in_repo = [f for _, f in uploads]
    resp = srequest(
        session,
        'POST', f"https://huggingface.co/api/{repo_type}s/{repo_id}/paths-info/{revision}",
        json={"paths": files_in_repo},
    )
    online_file_info = {tuple(to_segments(item['path'])): item for item in resp.json()}

    checks = []
    for f_in_local, f_in_repo in uploads:
        fs_in_repo = tuple(to_segments(f_in_repo))
        f_meta = online_file_info.get(fs_in_repo, None)
        if not f_meta:
            if f_in_local is not None:  # not exist in repo, need to upload
                checks.append((True, 'file'))
            else:  # not exist in repo, do not need to delete
                checks.append((False, None))
        else:
            if f_in_local is not None:  # going to upload
                if 'lfs' in f_meta:  # is a lfs file
                    is_lfs, oid, filesize = True, f_meta['lfs']['oid'], f_meta['lfs']['size']
                else:  # not lfs
                    is_lfs, oid, filesize = False, f_meta['oid'], f_meta['size']

                if f_meta['type'] != 'file':
                    raise FileExistsError(f'Path {f_meta["path"]!r} is a {f_meta["type"]} on huggingface, '
                                          f'unable to replace it with local file {f_in_local!r}.')
                _is_duplicated = _single_resource_is_duplicated(f_in_local, is_lfs, oid, filesize, chunk_for_hash)
                checks.append((not _is_duplicated, f_meta['type']))  # exist, need to upload if not the same
            else:  # going to delete
                checks.append((True, f_meta['type']))

    return checks


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
        self.repo_type = _check_repo_type(repo_type)
        self.revision = revision
        self.namespace = to_segments(namespace or [])
        self.session = get_requests_session()

    def path_join(self, path, *segments):
        return '/'.join((*self.namespace, path, *segments))

    def _file_url(self, file: List[str]):
        return hf_hub_url(self.repo, self.path_join(*file), repo_type=self.repo_type, revision=self.revision)

    def file_exists(self, file: List[str]) -> bool:
        resp = srequest(self.session, 'HEAD', self._file_url(file), raise_for_status=False)
        if resp.ok:  # file is here
            return True
        elif resp.status_code == 404:  # file not found
            return False
        else:  # network error
            resp.raise_for_status()  # pragma: no cover

    def read_text(self, file: List[str], encoding: str = 'utf-8') -> str:
        return srequest(self.session, 'GET', self._file_url(file)).content.decode(encoding=encoding)

    def batch_change_files(self, changes: List[Tuple[Optional[str], List[str]]]):
        _register_session_for_hf()

        _map_changes = {}
        for local_filename, file_in_repo in changes:
            sg = tuple(file_in_repo)
            if sg in _map_changes:
                fip = self.path_join(*file_in_repo)
                if _map_changes[sg] is None:
                    warnings.warn(f'Deletion of resource {fip!r} is not necessary, will be ignored.')
                else:
                    warnings.warn(f'Uploading of local resource {_map_changes[sg]!r} to {fip!r} '
                                  f'is not necessary, will be ignored.')

            _map_changes[sg] = local_filename

        uploads = [
            (local_filename, self.path_join(*file_in_repo))
            for file_in_repo, local_filename in _map_changes.items()
        ]
        uploads_is_needed = hf_local_upload_check(uploads, self.repo, self.repo_type, self.revision,
                                                  session=self.session)

        operations, op_items, additions, deletions = [], [], 0, 0
        for (local_filename, fip), (need, objtype) in zip(uploads, uploads_is_needed):
            if need:
                if local_filename is None:
                    if objtype == 'directory':  # a / should be at the end of path when deleting a folder
                        fip = f'{fip}/'
                        is_folder = True
                    else:
                        is_folder = False
                    operations.append(CommitOperationDelete(path_in_repo=fip, is_folder=is_folder))
                    op_items.append(f'-{fip}')
                    deletions += 1
                else:
                    operations.append(CommitOperationAdd(path_in_repo=fip, path_or_fileobj=local_filename))
                    op_items.append(f'+{fip}')
                    additions += 1

        if operations:
            current_time = datetime.datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')
            msg = ', '.join(sorted(op_items))
            commit_message = f"{msg}, on {current_time}"
            self.hf_client.create_commit(
                self.repo, operations,
                commit_message=commit_message,
                repo_type=self.repo_type,
                revision=self.revision,
            )
            return additions, deletions, commit_message
        else:
            return additions, deletions, None
