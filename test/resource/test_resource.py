import re
from copy import deepcopy
from typing import List, Union, Iterable, Tuple, Any, Mapping

import pytest
from gchar.games.arknights import Character

from hfmirror.resource import SyncResource, MetadataItem, SyncItem, SyncTree, RemoteSyncItem
from hfmirror.utils import TargetPathType


class ArknightsSkinResource(SyncResource):
    def __init__(self, chs: List[Character]):
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
    chs = [ch for ch in Character.all(contains_extra=False) if ch.rarity == 3 and ch.gender == 'male']
    return ArknightsSkinResource(chs)


@pytest.fixture(scope='module')
def arknights_sync_steward_metadata(arknights_sync):
    for item in arknights_sync.iter_sync_items():
        if isinstance(item, MetadataItem) and item.segments == ['PA42']:
            return item
    else:
        return None


@pytest.fixture(scope='module')
def arknights_sync_steward_skin_0(arknights_sync):
    for item in arknights_sync.iter_sync_items():
        if isinstance(item, SyncItem) and item.segments == ['PA42', '默认服装_精英零.png']:
            return item
    else:
        return None


@pytest.fixture(scope='module')
def arknights_sync_tree(arknights_sync):
    return arknights_sync.sync_tree()


@pytest.fixture()
def arknights_sync_tree_repr():
    return """
<root>        
[Metadata]        
text: 'global metadata'
├── PA42      
│   [Metadata]        
│   cnname: '史都华德'                                                                                                                                                                                     
│   enname: 'steward'          
│   id: 'PA42'                       
│   jpname: 'スチュワード'                                                                                                                                                                                 
│   ├── 风雪邀请.png --> <RemoteSyncItem url: 'https://prts.wiki///images/f/fe/%E7%AB%8B%E7%BB%98_%E5%8F%B2%E9%83%BD%E5%8D%8E%E5%BE%B7_skin1.png'>
│   │                [Metadata]                   
│   │                name: '风雪邀请'
│   └── 默认服装_精英零.png --> <RemoteSyncItem url: 'https://prts.wiki///images/4/44/%E7%AB%8B%E7%BB%98_%E5%8F%B2%E9%83%BD%E5%8D%8E%E5%BE%B7_1.png'>
│                        [Metadata]
│                        name: '默认服装 - 精英零'
├── PA43                                                                                                                                                                                                   
│   [Metadata]                                                                                       
│   cnname: '安赛尔'                                                                                                                                                                                       
│   enname: 'ansel'                                                                                  
│   id: 'PA43'
│   jpname: 'アンセル'                                                                               
│   ├── 悠然假日_HDm06.png --> <RemoteSyncItem url: 'https://prts.wiki///images/8/8a/%E7%AB%8B%E7%BB%98_%E5%AE%89%E8%B5%9B%E5%B0%94_skin1.png'>                                                  
│   │                      [Metadata]                                                                                                                                                                      
│   │                      name: '悠然假日 HDm06'
│   └── 默认服装_精英零.png --> <RemoteSyncItem url: 'https://prts.wiki///images/e/e4/%E7%AB%8B%E7%BB%98_%E5%AE%89%E8%B5%9B%E5%B0%94_1.png'>
│                        [Metadata]
│                        name: '默认服装 - 精英零'                                                   
├── PA44                                                                                             
│   [Metadata]                                                                                       
│   cnname: '安德切尔'                                                                               
│   enname: 'adnachiel'                                                                              
│   id: 'PA44'                                                                                       
│   jpname: 'アドナキエル'                                                                                                                                                                                 
│   ├── 无痕行者.png --> <RemoteSyncItem url: 'https://prts.wiki///images/2/22/%E7%AB%8B%E7%BB%98_%E5%AE%89%E5%BE%B7%E5%88%87%E5%B0%94_skin1.png'>
│   │                [Metadata]                                                                      
│   │                name: '无痕行者'    
│   └── 默认服装_精英零.png --> <RemoteSyncItem url: 'https://prts.wiki///images/9/94/%E7%AB%8B%E7%BB%98_%E5%AE%89%E5%BE%B7%E5%88%87%E5%B0%94_1.png'>
│                        [Metadata]                                                                                                                                                                        
│                        name: '默认服装 - 精英零'                                                   
├── PA62
│   [Metadata]
│   cnname: '月见夜'
│   enname: 'midnight'
│   id: 'PA62'
│   jpname: 'ミッドナイト'
│   ├── 第七夜苏醒魔君.png --> <RemoteSyncItem url: 'https://prts.wiki///images/3/34/%E7%AB%8B%E7%BB%98_%E6%9C%88%E8%A7%81%E5%A4%9C_skin1.png'>
│   │                   [Metadata]
│   │                   name: '第七夜苏醒魔君'
│   └── 默认服装_精英零.png --> <RemoteSyncItem url: 'https://prts.wiki///images/0/02/%E7%AB%8B%E7%BB%98_%E6%9C%88%E8%A7%81%E5%A4%9C_1.png'>
│                        [Metadata]
│                        name: '默认服装 - 精英零'
└── PA64
    [Metadata]
    cnname: '斑点'
    enname: 'spot'
    id: 'PA64'
    jpname: 'スポット'
    ├── 专业人士.png --> <RemoteSyncItem url: 'https://prts.wiki///images/e/e9/%E7%AB%8B%E7%BB%98_%E6%96%91%E7%82%B9_skin1.png'>
    │                [Metadata]
    │                name: '专业人士'
    └── 默认服装_精英零.png --> <RemoteSyncItem url: 'https://prts.wiki///images/8/8a/%E7%AB%8B%E7%BB%98_%E6%96%91%E7%82%B9_1.png'>
                         [Metadata]
                         name: '默认服装 - 精英零'
        """.strip()


@pytest.mark.unittest
class TestResourceResource:
    def test_custom_sync(self, arknights_sync_steward_metadata):
        assert arknights_sync_steward_metadata is not None
        assert arknights_sync_steward_metadata.segments == ['PA42']
        assert arknights_sync_steward_metadata.data == {
            "id": "PA42",
            "cnname": "史都华德",
            "jpname": "スチュワード",
            "enname": "steward",
        }
        assert arknights_sync_steward_metadata == arknights_sync_steward_metadata
        assert arknights_sync_steward_metadata == MetadataItem({
            "id": "PA42",
            "cnname": "史都华德",
            "jpname": "スチュワード",
            "enname": "steward",
        }, ['PA42'])
        assert arknights_sync_steward_metadata != None
        assert arknights_sync_steward_metadata != 1

        assert hash(arknights_sync_steward_metadata) == hash(MetadataItem({
            "id": "PA42",
            "cnname": "史都华德",
            "jpname": "スチュワード",
            "enname": "steward",
        }, ['PA42']))
        assert hash(arknights_sync_steward_metadata) != hash(None)
        assert hash(arknights_sync_steward_metadata) != hash(1)

        assert repr(arknights_sync_steward_metadata) == \
               "<MetadataItem data: {'id': 'PA42', 'cnname': '史都华德', 'jpname': 'スチュワード', 'enname': 'steward'}>"

    def test_sync_item(self, arknights_sync_steward_skin_0):
        assert arknights_sync_steward_skin_0 is not None
        assert isinstance(arknights_sync_steward_skin_0, SyncItem)
        assert arknights_sync_steward_skin_0.segments == ['PA42', '默认服装_精英零.png']

    def test_sync_tree(self, arknights_sync_tree, text_align, arknights_sync_tree_repr):
        assert arknights_sync_tree is not None
        assert isinstance(arknights_sync_tree, SyncTree)
        assert arknights_sync_tree.metadata == {'text': 'global metadata'}
        text_align.assert_equal(repr(arknights_sync_tree), arknights_sync_tree_repr)

        assert arknights_sync_tree == arknights_sync_tree
        assert arknights_sync_tree == deepcopy(arknights_sync_tree)
        assert arknights_sync_tree != None
        assert arknights_sync_tree != 1

        assert hash(arknights_sync_tree) == hash(deepcopy(arknights_sync_tree))
        assert hash(arknights_sync_tree) != hash(None)
        assert hash(arknights_sync_tree) != hash(1)

    def test_sync_tree_errors(self):
        class MySyncResource1(SyncResource):
            def grab(self) -> Iterable[Union[
                Tuple[str, Any, TargetPathType, Mapping],
                Tuple[str, Any, TargetPathType],
            ]]:
                yield 'f', 'f', 'f/1', {}

        with pytest.raises(KeyError):
            _ = MySyncResource1().sync_tree()

        class MySyncResource2(SyncResource):
            def grab(self) -> Iterable[Union[
                Tuple[str, Any, TargetPathType, Mapping],
                Tuple[str, Any, TargetPathType],
            ]]:
                yield 233

        with pytest.raises(TypeError):
            _ = MySyncResource2().sync_tree()

        class MySyncResource3(SyncResource):
            def grab(self) -> Iterable[Union[
                Tuple[str, Any, TargetPathType, Mapping],
                Tuple[str, Any, TargetPathType],
            ]]:
                yield 'remote', 'https://www.baidu.com', 'f/1.html', {}, 'fff'

        with pytest.raises(ValueError):
            _ = MySyncResource3().sync_tree()

        class MySyncResource4(SyncResource):
            def grab(self) -> Iterable[Union[
                Tuple[str, Any, TargetPathType, Mapping],
                Tuple[str, Any, TargetPathType],
            ]]:
                yield 'metadata', {'a': 1, 'b': [2, 3]}, 'f', {'c': 2}

        with pytest.warns(Warning):
            tree4 = MySyncResource4().sync_tree()
            assert tree4.items['f'].metadata == {'a': 1, 'b': [2, 3]}
            assert 'c' not in tree4.items['f'].metadata

        class MySyncResource5(SyncResource):
            def grab(self) -> Iterable[Union[
                Tuple[str, Any, TargetPathType, Mapping],
                Tuple[str, Any, TargetPathType],
            ]]:
                yield 'remote', 'https://www.baidu.com', 'f/1.html', {}
                yield 'remote', 'https://www.baidu.com', 'f', {}

        with pytest.raises(TypeError):
            _ = MySyncResource5().sync_tree()

        class MySyncResource6(SyncResource):
            def grab(self) -> Iterable[Union[
                Tuple[str, Any, TargetPathType, Mapping],
                Tuple[str, Any, TargetPathType],
            ]]:
                yield 'remote', 'https://www.baidu.com', 'f', {}
                yield 'remote', 'https://www.baidu.com', 'f/1.html', {}

        with pytest.raises(TypeError):
            _ = MySyncResource6().sync_tree()

        class MySyncResource6(SyncResource):
            def grab(self) -> Iterable[Union[
                Tuple[str, Any, TargetPathType, Mapping],
                Tuple[str, Any, TargetPathType],
            ]]:
                yield 'remote', 'https://www.baidu.com', 'f/1.html', {'a': 20, 'c': 5}
                yield 'metadata', {'a': 1, 'b': 2}, 'f/1.html'

        assert MySyncResource6().sync_tree().items['f'].items['1.html'].metadata == {'a': 1, 'b': 2, 'c': 5}

        class MySyncResource7(SyncResource):
            def grab(self) -> Iterable[Union[
                Tuple[str, Any, TargetPathType, Mapping],
                Tuple[str, Any, TargetPathType],
            ]]:
                yield 'remote', 'https://www.baidu.com', 'f/1.html', {'a': 20, 'c': 5}
                yield 'metadata', {'a': 1, 'b': 2}, 'f/1.html/34444'

        with pytest.raises(TypeError):
            _ = MySyncResource7().sync_tree()

        class MySyncResource8(SyncResource):
            def grab(self) -> Iterable[Union[
                Tuple[str, Any, TargetPathType, Mapping],
                Tuple[str, Any, TargetPathType],
            ]]:
                yield 'remote', 'https://www.baidu.com', 'f/1.html', {'a': 20, 'c': 5}
                yield 'remote', 'https://www.baidu.com/1', 'f/1.html', {'a': 1, 'b': 2}

        with pytest.warns(Warning):
            item = MySyncResource8().sync_tree().items['f'].items['1.html']
            assert isinstance(item, RemoteSyncItem)
            assert item.url == 'https://www.baidu.com/1'
            assert item.segments == ['f', '1.html']
            assert item.metadata == {'a': 1, 'b': 2}
