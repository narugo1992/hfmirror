import pytest
from hbutils.testing import disable_output

from hfmirror.resource import LocalDirectoryResource
from ..testing import TESTFILE_DIR


@pytest.fixture(scope='module')
def testfile_directory():
    return LocalDirectoryResource(TESTFILE_DIR)


@pytest.fixture(scope='module')
def testfile_directory_tree(testfile_directory):
    with disable_output():
        return testfile_directory.sync_tree()


@pytest.mark.unittest
class TestResourceLocal:
    def test_local_resource_basic(self, testfile_directory, testfile_directory_tree):
        assert testfile_directory.directory == TESTFILE_DIR

        assert testfile_directory_tree.metadata == {}
        assert set(testfile_directory_tree.items.keys()) == \
               {'.keep', '无痕行者.png', 'example_text.txt', 'subdirectory'}
        assert set(testfile_directory_tree.items['subdirectory'].items.keys()) == {'README.md'}
