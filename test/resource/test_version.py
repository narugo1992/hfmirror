from typing import Iterable, Union, Tuple, Any, Mapping

import pytest

from hfmirror.resource import VersionBasedResource
from hfmirror.utils import TargetPathType


class MyVersionResource(VersionBasedResource):
    def grab_for_items(self) -> Iterable[Union[
        Tuple[str, Any, TargetPathType, Mapping],
        Tuple[str, Any, TargetPathType],
    ]]:
        yield 'version', '0.0.1', ['0.0.1']
        yield 'version', 'latest', ['latest']
        yield 'version', '0.0.2', ['0.0.2']
        yield 'version', 'sss-0.1.0', ['sss-0.1.0']


@pytest.fixture()
def my_v_res():
    return MyVersionResource()


@pytest.mark.unittest
class TestResourceVersion:
    def test_version(self, my_v_res):
        with pytest.warns(Warning):
            my_v_tree = my_v_res.sync_tree()
        assert 'LATEST_RELEASE_0.0.1' in my_v_tree.items
        assert 'LATEST_RELEASE_0.0.2' in my_v_tree.items
        assert 'LATEST_RELEASE_0.1.0' in my_v_tree.items
        assert 'LATEST_RELEASE_sss-0.1.0' not in my_v_tree.items
        assert 'LATEST_RELEASE_latest' not in my_v_tree.items

    def test_failed_version(self):
        class FailedVersionResource(MyVersionResource):
            __version_pattern__ = r'(?P<version>[\s\S]+)'

            def grab_for_items(self) -> Iterable[Union[
                Tuple[str, Any, TargetPathType, Mapping],
                Tuple[str, Any, TargetPathType],
            ]]:
                yield 'version', '0.0.1', ['0.0.1']
                yield 'version', '0.0.2', ['0.0.2']
                yield 'version', '0.1.0.sss', ['sss-0.1.0']

        FailedVersionResource().sync_tree()
