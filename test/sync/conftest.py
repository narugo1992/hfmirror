import os.path
import re
from typing import List, Union, Iterable, Tuple, Any, Mapping

import pytest
from gchar.games.arknights import Character
from hbutils.testing import isolated_directory

from hfmirror.resource import SyncResource
from hfmirror.storage import LocalStorage
from hfmirror.utils import TargetPathType


@pytest.fixture()
def isolated_storage():
    with isolated_directory():
        yield LocalStorage(os.path.abspath('.'))


class ArknightsSkinResource(SyncResource):
    def __init__(self, chs: List[Character]):
        SyncResource.__init__(self)
        self.characters = chs

    def grab(self) -> Iterable[Union[
        Tuple[str, Any, TargetPathType, Mapping],
        Tuple[str, Any, TargetPathType],
    ]]:
        for ch in self.characters:
            metadata = {
                'id': ch.index,
                'cnname': str(ch.cnname) if ch.cnname else None,
                'jpname': str(ch.jpname) if ch.jpname else None,
                'enname': str(ch.enname) if ch.enname else None,
            }
            yield 'metadata', metadata, ch.index

            for skin in ch.skins:
                filename = re.sub(r'\W+', '_', skin.name).strip('_') + '.png'
                yield 'remote', skin.url, f'{ch.index}/{filename}', {'name': skin.name}

        yield 'metadata', {'text': 'global metadata'}, ''


@pytest.fixture(scope='module')
def arknights_sync():
    chs = [ch for ch in Character.all(contains_extra=False) if ch.rarity == 3 and ch.gender == 'male'][:3]
    return ArknightsSkinResource(chs)


@pytest.fixture(scope='module')
def arknights_sync_large():
    chs = [ch for ch in Character.all(contains_extra=False) if ch.rarity == 3]
    return ArknightsSkinResource(chs)
