import glob
import os

import pytest
from gchar.games.arknights import Character

from hfmirror.sync import SyncTask


@pytest.fixture()
def sync_for_arknights_skins(arknights_sync, isolated_storage):
    yield SyncTask(arknights_sync, isolated_storage)


@pytest.fixture()
def sync_for_arknights_skins_b10(arknights_sync, isolated_storage):
    yield SyncTask(arknights_sync, isolated_storage, batch=10)


@pytest.fixture()
def sync_for_arknights_skins_large_b10(arknights_sync_large, isolated_storage):
    yield SyncTask(arknights_sync_large, isolated_storage, batch=10)


@pytest.mark.unittest
class TestSyncSync:

    def test_sync(self, sync_for_arknights_skins):
        sync_for_arknights_skins.sync()
        assert os.path.exists('PA42')
        assert os.path.exists(os.path.join('PA42', '风雪邀请.png'))
        assert os.path.getsize(os.path.join('PA42', '风雪邀请.png')) == 890024
        assert os.path.exists(os.path.join('PA42', '默认服装_精英零.png'))
        assert os.path.getsize(os.path.join('PA42', '默认服装_精英零.png')) == 258396

        sync_for_arknights_skins.sync()
        assert os.path.exists('PA42')
        assert os.path.exists(os.path.join('PA42', '风雪邀请.png'))
        assert os.path.getsize(os.path.join('PA42', '风雪邀请.png')) == 890024
        assert os.path.exists(os.path.join('PA42', '默认服装_精英零.png'))
        assert os.path.getsize(os.path.join('PA42', '默认服装_精英零.png')) == 258396

    def test_sync_with_batch_10(self, sync_for_arknights_skins_large_b10, sync_for_arknights_skins_b10):
        sync_for_arknights_skins_large_b10.sync()
        assert os.path.exists('PA42')
        assert os.path.exists(os.path.join('PA42', '风雪邀请.png'))
        assert os.path.getsize(os.path.join('PA42', '风雪邀请.png')) == 890024
        assert os.path.exists(os.path.join('PA42', '默认服装_精英零.png'))
        assert os.path.getsize(os.path.join('PA42', '默认服装_精英零.png')) == 258396

        for ch in Character.all(contains_extra=False):
            if ch.rarity == 3:
                assert os.path.exists(ch.index), f'Character {ch!r}\'s directory not exist.'
                assert len(glob.glob(os.path.join(ch.index, '*.png'))) >= 1, \
                    f'Character {ch!r} directory not contain skins!'

        sync_for_arknights_skins_b10.sync()
        assert os.path.exists('PA42')
        assert os.path.exists(os.path.join('PA42', '风雪邀请.png'))
        assert os.path.getsize(os.path.join('PA42', '风雪邀请.png')) == 890024
        assert os.path.exists(os.path.join('PA42', '默认服装_精英零.png'))
        assert os.path.getsize(os.path.join('PA42', '默认服装_精英零.png')) == 258396

        ch_indexs = [ch.index for ch in Character.all(contains_extra=False)
                     if ch.rarity == 3 and ch.gender == 'male'][:3]
        for ch in Character.all(contains_extra=False):
            if ch.rarity == 3:
                if ch.index in ch_indexs:
                    assert os.path.exists(ch.index), f'Character {ch!r}\'s directory not exist.'
                    assert len(glob.glob(os.path.join(ch.index, '*.png'))) >= 1, \
                        f'Character {ch!r} directory not contain skins!'
                else:
                    assert not os.path.exists(ch.index), f'Character {ch!r}\'s directory not removed.'
