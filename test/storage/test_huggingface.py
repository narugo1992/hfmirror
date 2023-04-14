import os
import pathlib

import pytest
from hbutils.testing import OS
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

        additions, deletions, message = hf_storage.batch_change_files([
            ('example_text.txt', ['f.txt']),
            ('example_text.txt', ['2', 'f.txt']),
            ('.keep', ['2', 'f2.txt']),
        ])
        assert (additions, deletions) == (3, 0)
        assert hf_storage.file_exists(['f.txt'])
        assert hf_storage.file_exists(['2', 'f.txt'])
        assert hf_storage.file_exists(['2', 'f2.txt'])
        assert not hf_storage.file_exists(['2', 'fx.txt'])
        assert hf_storage.read_text(['f.txt']) == \
               pathlib.Path('example_text.txt').read_text(encoding='utf-8')
        assert hf_storage.read_text(['2', 'f.txt']) == \
               pathlib.Path('example_text.txt').read_text(encoding='utf-8')
        assert hf_storage.read_text(['2', 'f2.txt']) == \
               pathlib.Path('.keep').read_text(encoding='utf-8')

        with pytest.warns(Warning):
            additions, deletions, message = hf_storage.batch_change_files([
                (None, ['2', 'f.txt']),
                ('.keep', ['2', 'fx.txt']),
                (None, ['2', 'f2.txt']),
                ('example_text.txt', ['4', 'root', 'f.txt']),
                ('example_text.txt', ['2', 'f2.txt']),
                ('无痕行者.png', ['无痕行者.png']),
            ])
        assert (additions, deletions) == (3, 1)
        assert hf_storage.file_exists(['f.txt'])
        assert not hf_storage.file_exists(['2', 'f.txt'])
        assert hf_storage.file_exists(['2', 'f2.txt'])
        assert hf_storage.file_exists(['2', 'fx.txt'])
        assert hf_storage.file_exists(['4', 'root', 'f.txt'])
        assert hf_storage.read_text(['f.txt']) == \
               pathlib.Path('example_text.txt').read_text(encoding='utf-8')
        assert hf_storage.read_text(['2', 'f2.txt']) == \
               pathlib.Path('example_text.txt').read_text(encoding='utf-8')
        assert hf_storage.read_text(['2', 'fx.txt']) == \
               pathlib.Path('.keep').read_text(encoding='utf-8')
        assert hf_storage.read_text(['4', 'root', 'f.txt']) == \
               pathlib.Path('example_text.txt').read_text(encoding='utf-8')

        with pytest.raises(FileExistsError):
            hf_storage.batch_change_files([
                ('example_text.txt', ['2']),
            ])

        # still a bug on windows
        # see: https://github.com/narugo1992/hfmirror/issues/1
        if not OS.windows:
            with pytest.warns(Warning):
                additions, deletions, message = hf_storage.batch_change_files([
                    (None, ['2', 'f.txt']),
                    ('.keep', ['2', 'fx.txt']),
                    ('.keep', ['2', 'fx.txt']),
                    ('example_text.txt', ['4', 'root', 'f.txt']),
                    ('example_text.txt', ['2', 'f2.txt']),
                ])
            assert (additions, deletions) == (0, 0)
            assert message is None

            additions, deletions, message = hf_storage.batch_change_files([
                (None, ['2', 'f2.txt']),
                (None, ['4']),
            ])
            assert (additions, deletions) == (0, 2)
            assert not hf_storage.file_exists(['2', 'f2.txt'])
            assert not hf_storage.file_exists(['4', 'root', 'f.txt'])

    def test_hf_warning(self, huggingface_client, huggingface_access_token):
        with pytest.warns(Warning):
            st = HuggingfaceStorage('narugo/gchar', hf_client=huggingface_client, access_token=huggingface_access_token)
            assert st.hf_client is huggingface_client

    def test_hf_invalid_type(self):
        with pytest.raises(ValueError):
            _ = HuggingfaceStorage('narugo/gchar', repo_type='what_the_fxxk')
