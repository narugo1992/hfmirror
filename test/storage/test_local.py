import os.path
import pathlib

import pytest
from hbutils.system import TemporaryDirectory

from hfmirror.storage import LocalStorage
from test.testing import isolated_to_testfile


@pytest.fixture()
def _d_isolated_storage():
    with TemporaryDirectory() as td:
        yield LocalStorage(td), td


@pytest.fixture()
def isolated_storage(_d_isolated_storage):
    storage, _ = _d_isolated_storage
    yield storage


@pytest.fixture()
def isolated_directory(_d_isolated_storage):
    _, directory = _d_isolated_storage
    yield directory


@pytest.mark.unittest
class TestStorageLocal:
    @isolated_to_testfile()
    def test_storage_local(self, isolated_storage, isolated_directory):
        assert isolated_storage.root_directory == isolated_directory
        assert isolated_storage.namespace == []
        assert not isolated_storage.file_exists(['1.txt'])

        isolated_storage.batch_change_files([
            ('example_text.txt', ['f.txt']),
            ('example_text.txt', ['2', 'f.txt']),
            ('.keep', ['2', 'f2.txt']),
        ])
        assert os.path.exists(os.path.join(isolated_directory, 'f.txt'))
        assert os.path.exists(os.path.join(isolated_directory, '2', 'f.txt'))
        assert os.path.exists(os.path.join(isolated_directory, '2', 'f2.txt'))
        assert not os.path.exists(os.path.join(isolated_directory, '2', 'fx.txt'))
        assert isolated_storage.file_exists(['f.txt'])
        assert isolated_storage.file_exists(['2', 'f.txt'])
        assert isolated_storage.file_exists(['2', 'f2.txt'])
        assert not isolated_storage.file_exists(['2', 'fx.txt'])
        assert isolated_storage.read_text(['f.txt']) == \
               pathlib.Path('example_text.txt').read_text(encoding='utf-8')
        assert isolated_storage.read_text(['2', 'f.txt']) == \
               pathlib.Path('example_text.txt').read_text(encoding='utf-8')
        assert isolated_storage.read_text(['2', 'f2.txt']) == \
               pathlib.Path('.keep').read_text(encoding='utf-8')

        isolated_storage.batch_change_files([
            (None, ['2', 'f.txt']),
            ('.keep', ['2', 'fx.txt']),
            ('example_text.txt', ['4', 'root', 'f.txt']),
            ('example_text.txt', ['2', 'f2.txt']),
        ])
        assert os.path.exists(os.path.join(isolated_directory, 'f.txt'))
        assert not os.path.exists(os.path.join(isolated_directory, '2', 'f.txt'))
        assert os.path.exists(os.path.join(isolated_directory, '2', 'f2.txt'))
        assert os.path.exists(os.path.join(isolated_directory, '2', 'fx.txt'))
        assert os.path.exists(os.path.join(isolated_directory, '4', 'root', 'f.txt'))
        assert isolated_storage.file_exists(['f.txt'])
        assert not isolated_storage.file_exists(['2', 'f.txt'])
        assert isolated_storage.file_exists(['2', 'f2.txt'])
        assert isolated_storage.file_exists(['2', 'fx.txt'])
        assert isolated_storage.file_exists(['4', 'root', 'f.txt'])
        assert isolated_storage.read_text(['f.txt']) == \
               pathlib.Path('example_text.txt').read_text(encoding='utf-8')
        assert isolated_storage.read_text(['2', 'f2.txt']) == \
               pathlib.Path('example_text.txt').read_text(encoding='utf-8')
        assert isolated_storage.read_text(['2', 'fx.txt']) == \
               pathlib.Path('.keep').read_text(encoding='utf-8')
        assert isolated_storage.read_text(['4', 'root', 'f.txt']) == \
               pathlib.Path('example_text.txt').read_text(encoding='utf-8')

        # make sure the operation is atomic
        # the former operations will be rollback when the later one is failed.
        with pytest.raises(FileNotFoundError):
            isolated_storage.batch_change_files([
                (None, ['2', 'fx.txt']),
                ('.keep', ['2', 'f2.txt']),
                ('.keep', ['2', 'f2t.txt']),
                ('file_not_exist', ['1.txt']),  # this operation will fail
            ])
        assert os.path.exists(os.path.join(isolated_directory, 'f.txt'))
        assert not os.path.exists(os.path.join(isolated_directory, '2', 'f.txt'))
        assert os.path.exists(os.path.join(isolated_directory, '2', 'f2.txt'))
        assert os.path.exists(os.path.join(isolated_directory, '2', 'fx.txt'))
        assert os.path.exists(os.path.join(isolated_directory, '4', 'root', 'f.txt'))
        assert not os.path.exists(os.path.join(isolated_directory, '2', 'f2t.txt'))
        assert not os.path.exists(os.path.join(isolated_directory, '1.txt'))
        assert isolated_storage.file_exists(['f.txt'])
        assert not isolated_storage.file_exists(['2', 'f.txt'])
        assert isolated_storage.file_exists(['2', 'f2.txt'])
        assert isolated_storage.file_exists(['2', 'fx.txt'])
        assert isolated_storage.file_exists(['4', 'root', 'f.txt'])
        assert not isolated_storage.file_exists(['2', 'f2t.txt'])
        assert not isolated_storage.file_exists(['1.txt'])
        assert isolated_storage.read_text(['f.txt']) == \
               pathlib.Path('example_text.txt').read_text(encoding='utf-8')
        assert isolated_storage.read_text(['2', 'f2.txt']) == \
               pathlib.Path('example_text.txt').read_text(encoding='utf-8')
        assert isolated_storage.read_text(['2', 'fx.txt']) == \
               pathlib.Path('.keep').read_text(encoding='utf-8')
        assert isolated_storage.read_text(['4', 'root', 'f.txt']) == \
               pathlib.Path('example_text.txt').read_text(encoding='utf-8')
