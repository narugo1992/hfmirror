import os
import pathlib

import pytest
from huggingface_hub import CommitOperationAdd

from hfmirror.storage import HuggingfaceStorage
from ..testing import TESTFILE_DIR, isolated_to_testfile


@pytest.fixture()
def repo_like_testfile(huggingface_repo, huggingface_client):
    operations = []
    for item in os.listdir(TESTFILE_DIR):
        operations.append(CommitOperationAdd(
            path_in_repo=item,
            path_or_fileobj=os.path.join(TESTFILE_DIR, item),
        ))

    huggingface_client.create_commit(
        huggingface_repo, operations,
        commit_message='init repo',
        repo_type='dataset', revision='main',
    )

    yield huggingface_repo


@pytest.fixture()
def hf_storage(repo_like_testfile, huggingface_client):
    yield HuggingfaceStorage(repo_like_testfile, hf_client=huggingface_client)


@pytest.mark.unittest
class TestStorageHuggingface:
    def test_see_repo(self, repo_like_testfile, huggingface_client):
        assert repo_like_testfile
        files = huggingface_client.list_repo_files(repo_like_testfile, repo_type='dataset')
        assert '.keep' in files
        assert 'example_text.txt' in files
        assert '.gitattributes' in files

    @isolated_to_testfile()
    def test_hf_storage(self, hf_storage):
        assert hf_storage.file_exists(['.keep'])
        assert hf_storage.file_exists(['example_text.txt'])
        assert hf_storage.file_exists(['.gitattributes'])
        assert not hf_storage.file_exists(['2', 'example_text.txt'])

        assert hf_storage.read_text(['.keep']) == pathlib.Path('.keep').read_text(encoding='utf-8')
        assert hf_storage.read_text(['example_text.txt']) == \
               pathlib.Path('example_text.txt').read_text(encoding='utf-8')
