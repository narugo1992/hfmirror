import os
import pathlib
import time
from hashlib import sha256

import pytest

from hfmirror.resource import RemoteSyncItem, ResourceNotChange, TextOutputSyncItem


@pytest.fixture()
def nian_skin_url(url_to_game_character_skins):
    return f'{url_to_game_character_skins}/arknights/NM01/乐逍遥.png'


@pytest.fixture()
def nian_mark():
    return {
        'url': 'https://huggingface.co/datasets/deepghs/game_character_skins/resolve/main/arknights/NM01/乐逍遥.png',
        'etag': '"7f9608c447fd74878ec33714d2a81e0c"',
        'expires': None,
        'content_length': 3832280,
        'content_type': 'image/png',
    }


@pytest.mark.unittest
class TestResourceItem:
    def test_remote_sync_item(self, nian_skin_url, nian_mark):
        item = RemoteSyncItem(nian_skin_url, {'name': '年'}, ['nian', 'lexiaoyao.png'])
        assert item.url == nian_skin_url
        assert item.metadata == {'name': '年'}
        assert item.segments == ['nian', 'lexiaoyao.png']

        assert item.refresh_mark(None) == nian_mark
        with pytest.raises(ResourceNotChange):
            item.refresh_mark(nian_mark)
        with pytest.raises(ResourceNotChange):
            item.refresh_mark({**nian_mark, 'expires': time.time() + 10000})

        with item.load_file() as file:
            sha = sha256()
            with open(file, 'rb') as f:
                while True:
                    chunk = f.read(2048)
                    if not chunk:
                        break
                    sha.update(chunk)

            assert os.path.getsize(file) == 3832280
            assert sha.hexdigest() == '3333af134d03375958b54d88193dcddfad3a0dd3135bbfd3a6c0988938049073'

        assert item == item
        assert item == RemoteSyncItem(nian_skin_url, {'name': '年'}, ['nian', 'lexiaoyao.png'])
        assert item != RemoteSyncItem(nian_skin_url, {'name': '年x'}, ['nian', 'lexiaoyao.png'])
        assert item != RemoteSyncItem(nian_skin_url, {'name': '年'}, ['nian', 'lexiaoyao.p'])
        assert item != 2
        assert item != None

        assert hash(item) == hash(item)
        assert hash(item) == hash(RemoteSyncItem(nian_skin_url, {'name': '年'}, ['nian', 'lexiaoyao.png']))
        assert hash(item) != hash(RemoteSyncItem(nian_skin_url, {'name': '年x'}, ['nian', 'lexiaoyao.png']))
        assert hash(item) != hash(RemoteSyncItem(nian_skin_url, {'name': '年'}, ['nian', 'lexiaoyao.p']))

        assert repr(item) == '<RemoteSyncItem url: \'https://huggingface.co/datasets/deepghs/' \
                             'game_character_skins/resolve/main/arknights/NM01/乐逍遥.png\'>'

    def test_text_output_sync_item(self):
        item = TextOutputSyncItem('v0.8.2', {'v': '082'}, ['v0.8.2', 'version_info.json'])
        assert item.content == 'v0.8.2'
        assert item.metadata == {'v': '082'}
        assert item.segments == ['v0.8.2', 'version_info.json']

        with item.load_file() as file:
            assert pathlib.Path(file).read_text() == 'v0.8.2'

        assert repr(item) == '<TextOutputSyncItem content: \'v0.8.2\'>'

        assert item == item
        assert item == TextOutputSyncItem('v0.8.2', {'v': '082'}, ['v0.8.2', 'version_info.json'])
        assert item != TextOutputSyncItem('v0.8.2', {'v': '082'}, ['v0.8.2', 'version_info.jso'])
        assert item != TextOutputSyncItem('v0.8.2', {'f': '082'}, ['v0.8.2', 'version_info.json'])
        assert item != TextOutputSyncItem('v0.8.2 ', {'f': '082'}, ['v0.8.2', 'version_info.json'])
        assert item != RemoteSyncItem('v0.8.2 ', {'f': '082'}, ['v0.8.2', 'version_info.json'])
