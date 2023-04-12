import os

import pytest
from hbutils.testing import disable_output

from hfmirror.sync import SyncTask


@pytest.fixture()
def sync_for_arknights_skins(arknights_sync, isolated_storage):
    yield SyncTask(arknights_sync, isolated_storage)


@pytest.mark.unittest
class TestSyncSync:

    def test_sync(self, sync_for_arknights_skins):
        with disable_output():
            sync_for_arknights_skins.sync()
        assert os.path.exists('PA42')
        assert os.path.exists(os.path.join('PA42', '风雪邀请.png'))
        assert os.path.getsize(os.path.join('PA42', '风雪邀请.png')) == 890024
        assert os.path.exists(os.path.join('PA42', '默认服装_精英零.png'))
        assert os.path.getsize(os.path.join('PA42', '默认服装_精英零.png')) == 258396

        with disable_output():
            sync_for_arknights_skins.sync()
        assert os.path.exists('PA42')
        assert os.path.exists(os.path.join('PA42', '风雪邀请.png'))
        assert os.path.getsize(os.path.join('PA42', '风雪邀请.png')) == 890024
        assert os.path.exists(os.path.join('PA42', '默认服装_精英零.png'))
        assert os.path.getsize(os.path.join('PA42', '默认服装_精英零.png')) == 258396
