import os
import pathlib
import platform
import time
from contextlib import contextmanager
from hashlib import sha256
from typing import ContextManager

import pytest
from hbutils.collection import get_recovery_func, BaseRecovery
from hbutils.collection.recover import _OriginType, register_recovery
from hbutils.system import TemporaryDirectory

from hfmirror.resource import RemoteSyncItem, ResourceNotChange, TextOutputSyncItem, CustomSyncItem
from hfmirror.resource.item import register_sync_type, SyncItem, create_sync_item


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


class TypeRecovery(BaseRecovery):
    __rtype__ = (type,)

    def _recover(self):
        pass

    @classmethod
    def from_origin(cls, origin: _OriginType, recursive: bool = True) -> 'BaseRecovery':
        return cls(origin)


register_recovery(TypeRecovery)


@pytest.fixture(autouse=True)
def recover_sync_types():
    from hfmirror.resource.item import _REGISTERED_SYNC_TYPES
    func = get_recovery_func(_REGISTERED_SYNC_TYPES)
    try:
        yield
    finally:
        func()


@contextmanager
def show_sys():
    with TemporaryDirectory() as td:
        filename = os.path.join(td, 'sys')
        with open(filename, 'w') as f:
            f.write(platform.system())

        yield filename


class SysSyncItem(SyncItem):
    __type__ = 'sys'

    @contextmanager
    def load_file(self) -> ContextManager[str]:
        with show_sys() as f:
            yield f


class NoneSyncItem(SyncItem):
    @contextmanager
    def load_file(self) -> ContextManager[str]:
        with show_sys() as f:
            yield f


class MetadataSyncItem(SyncItem):
    __type__ = 'metadata'

    @contextmanager
    def load_file(self) -> ContextManager[str]:
        with show_sys() as f:
            yield f


class AlreadyExistSyncItem(SyncItem):
    __type__ = 'remote'

    @contextmanager
    def load_file(self) -> ContextManager[str]:
        with show_sys() as f:
            yield f


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

        assert item.refresh_mark(None) == {}
        assert item.refresh_mark({'a': 1}) == {'a': 1}

        with item.load_file() as file:
            assert pathlib.Path(file).read_text() == 'v0.8.2'

        assert repr(item) == '<TextOutputSyncItem content: \'v0.8.2\'>'

        assert item == item
        assert item == TextOutputSyncItem('v0.8.2', {'v': '082'}, ['v0.8.2', 'version_info.json'])
        assert item != TextOutputSyncItem('v0.8.2', {'v': '082'}, ['v0.8.2', 'version_info.jso '])
        assert item != TextOutputSyncItem('v0.8.2', {'f': '082'}, ['v0.8.2', 'version_info.json'])
        assert item != TextOutputSyncItem('v0.8._', {'v': '082'}, ['v0.8.2', 'version_info.json'])
        assert item != RemoteSyncItem('v0.8.2', {'v': '082'}, ['v0.8.2', 'version_info.json'])

    def test_custom_sync_item(self):
        item = CustomSyncItem(show_sys, {'sys': platform.system()}, ['sys', 'v'])
        assert item.gene is show_sys
        assert item.metadata == {'sys': platform.system()}
        assert item.segments == ['sys', 'v']

        assert item.refresh_mark(None) == {}
        assert item.refresh_mark({'a': 1}) == {'a': 1}

        with item.load_file() as file:
            assert pathlib.Path(file).read_text() == platform.system()

        assert repr(item).startswith('<CustomSyncItem gene: <function show_sys at')

        assert item == item
        assert item == CustomSyncItem(show_sys, {'sys': platform.system()}, ['sys', 'v'])
        assert item != CustomSyncItem(show_sys, {'sys': platform.system()}, ['sys', 'v1'])
        assert item != CustomSyncItem(show_sys, {'sy': platform.system()}, ['sys', 'v'])
        assert item != CustomSyncItem(lambda: None, {'sys': platform.system()}, ['sys', 'v'])
        assert item != RemoteSyncItem(show_sys, {'sys': platform.system()}, ['sys', 'v'])

    def test_register_custom(self):
        register_sync_type(SysSyncItem)
        item = SysSyncItem(None, {'sys': platform.system()}, ['sys', 'v'])
        assert item.metadata == {'sys': platform.system()}
        assert item.segments == ['sys', 'v']

        with item.load_file() as file:
            assert pathlib.Path(file).read_text() == platform.system()

        with pytest.raises(TypeError):
            register_sync_type(NoneSyncItem)
        with pytest.raises(KeyError):
            register_sync_type(MetadataSyncItem)
        with pytest.raises(KeyError):
            register_sync_type(AlreadyExistSyncItem)

    def test_create_sync_item(self, nian_skin_url):
        remote_item = create_sync_item('remote', nian_skin_url, {'name': '年'}, ['nian', 'lexiaoyao.png'])
        assert isinstance(remote_item, RemoteSyncItem)
        assert remote_item == \
               RemoteSyncItem(nian_skin_url, {'name': '年'}, ['nian', 'lexiaoyao.png'])

        text_item = create_sync_item('text', 'v0.8.2', {'v': '082'}, ['v0.8.2', 'version_info.json'])
        assert isinstance(text_item, TextOutputSyncItem)
        assert text_item == \
               TextOutputSyncItem('v0.8.2', {'v': '082'}, ['v0.8.2', 'version_info.json'])

        custom_item = create_sync_item('custom', show_sys, {'sys': platform.system()}, ['sys', 'v'])
        assert isinstance(custom_item, CustomSyncItem)
        assert custom_item == \
               CustomSyncItem(show_sys, {'sys': platform.system()}, ['sys', 'v'])

        register_sync_type(SysSyncItem)
        sys_item = create_sync_item('sys', None, {'sys': platform.system()}, ['sys', 'v'])
        assert isinstance(sys_item, SysSyncItem)
        assert sys_item.metadata == {'sys': platform.system()}
        assert sys_item.segments == ['sys', 'v']

        with pytest.raises(KeyError):
            _ = create_sync_item('fffff', None, {'sys': platform.system()}, ['sys', 'v'])
