import glob
import os

import pytest
from gchar.games.arknights import Character

from hfmirror.sync import SyncTask


@pytest.fixture()
def skin_sync_b0(arknights_sync, isolated_storage):
    yield SyncTask(arknights_sync, isolated_storage, batch=0)


@pytest.fixture()
def skin_sync_b10(arknights_sync, isolated_storage):
    yield SyncTask(arknights_sync, isolated_storage, batch=10)


@pytest.fixture()
def skin_sync_l_b10(arknights_sync_large, isolated_storage):
    yield SyncTask(arknights_sync_large, isolated_storage, batch=10)


@pytest.fixture()
def skin_sync_bx(arknights_sync, isolated_storage):
    yield SyncTask(arknights_sync, isolated_storage, batch=-1)


@pytest.fixture()
def skin_sync_l_bx(arknights_sync_large, isolated_storage):
    yield SyncTask(arknights_sync_large, isolated_storage, batch=-1)


# noinspection DuplicatedCode
@pytest.mark.unittest
class TestSyncSync:

    def test_sync(self, skin_sync_b0):
        skin_sync_b0.sync()
        assert os.path.exists('PA42')
        assert os.path.exists(os.path.join('PA42', '风雪邀请.png'))
        assert os.path.getsize(os.path.join('PA42', '风雪邀请.png')) == 890024
        assert os.path.exists(os.path.join('PA42', '默认服装_精英零.png'))
        assert os.path.getsize(os.path.join('PA42', '默认服装_精英零.png')) == 258396

        skin_sync_b0.sync()
        assert os.path.exists('PA42')
        assert os.path.exists(os.path.join('PA42', '风雪邀请.png'))
        assert os.path.getsize(os.path.join('PA42', '风雪邀请.png')) == 890024
        assert os.path.exists(os.path.join('PA42', '默认服装_精英零.png'))
        assert os.path.getsize(os.path.join('PA42', '默认服装_精英零.png')) == 258396

    def test_sync_with_batch_10(self, skin_sync_l_b10, skin_sync_b10):
        skin_sync_l_b10.sync()
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

        skin_sync_b10.sync()
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

    def test_sync_with_batch_x(self, skin_sync_l_bx, skin_sync_bx):
        skin_sync_l_bx.sync()
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

        skin_sync_bx.sync()
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
