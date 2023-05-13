from typing import Optional, List

import pytest

from hfmirror.resource import SourceForgeFilesResource


class CustomMirrorResource(SourceForgeFilesResource):
    def _get_version(self, type_, segments) -> Optional[str]:
        if len(segments) == 1:
            return segments[0]
        else:
            return None

    def _process_segments(self, type_, segments) -> Optional[List[str]]:
        if segments[0] == 'v0.0.3':
            return None
        else:
            return segments


@pytest.mark.unittest
class TestResourceSourceforge:
    def test_mirror_resource(self):
        resource = CustomMirrorResource('dghs-imgutils')
        tree = resource.sync_tree()
        assert 'LATEST_RELEASE' in tree.items
        assert 'LATEST_RELEASE_0' in tree.items
        assert 'LATEST_RELEASE_0.0.2' in tree.items
        assert 'LATEST_RELEASE_0.0.3' not in tree.items

        assert tree.items['LATEST_RELEASE_0'].content.startswith('v0.0.')
        assert tree.items['LATEST_RELEASE_0'].content != 'v0.0.3'
        assert tree.items['v0.0.2'].items['README.md'].refresh_mark(None) == {
            'url': 'https://downloads.sourceforge.net/project/dghs-imgutils/v0.0.2/README.md',
            'etag': '"6451fdc9-12f"',
            'expires': None,
            'content_length': 303,
            'content_type': 'application/octet-stream'
        }
        assert tree.items['v0.0.2'].items['dghs_imgutils-0.0.2-py3-none-any.whl'].refresh_mark(None) == {
            'url': 'https://downloads.sourceforge.net/project/dghs-imgutils/'
                   'v0.0.2/dghs_imgutils-0.0.2-py3-none-any.whl',
            'etag': '"6451fedf-a6d5"',
            'expires': None,
            'content_length': 42709,
            'content_type': 'application/octet-stream'
        }

    def test_native(self):
        resource = SourceForgeFilesResource('dghs-imgutils')
        tree = resource.sync_tree()
        assert 'LATEST_RELEASE' not in tree.items
        assert 'LATEST_RELEASE_0' not in tree.items
        assert 'LATEST_RELEASE_0.0.2' not in tree.items
        assert 'LATEST_RELEASE_0.0.3' not in tree.items
        assert 'LATEST_RELEASE_100' not in tree.items

        assert tree.items['v0.0.2'].items['README.md'].refresh_mark(None) == {
            'url': 'https://downloads.sourceforge.net/project/dghs-imgutils/v0.0.2/README.md',
            'etag': '"6451fdc9-12f"',
            'expires': None,
            'content_length': 303,
            'content_type': 'application/octet-stream'
        }
        assert tree.items['v0.0.2'].items['dghs_imgutils-0.0.2-py3-none-any.whl'].refresh_mark(None) == {
            'url': 'https://downloads.sourceforge.net/project/dghs-imgutils/'
                   'v0.0.2/dghs_imgutils-0.0.2-py3-none-any.whl',
            'etag': '"6451fedf-a6d5"',
            'expires': None,
            'content_length': 42709,
            'content_type': 'application/octet-stream'
        }
