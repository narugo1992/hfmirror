from typing import Optional, List

import pytest

from hfmirror.resource import SourceForgeFilesResource


class CheckstyleMirrorResource(SourceForgeFilesResource):
    def _get_version(self, type_, segments) -> Optional[str]:
        if len(segments) == 1:
            return segments[0]
        else:
            return None

    def _process_segments(self, type_, segments) -> Optional[List[str]]:
        if segments[0] > 'checkstyle-10.9.0':
            return None
        else:
            return segments


@pytest.mark.unittest
class TestResourceSourceforge:
    def test_mirror_resource(self):
        resource = CheckstyleMirrorResource('checkstyle.mirror')
        tree = resource.sync_tree()
        assert 'LATEST_RELEASE' in tree.items
        assert 'LATEST_RELEASE_10' in tree.items
        assert 'LATEST_RELEASE_10.9.0' in tree.items
        assert 'LATEST_RELEASE_10.9.1' not in tree.items

        assert tree.items['LATEST_RELEASE_10.9'].content == 'checkstyle-10.9.0'
        assert tree.items['checkstyle-10.9.0'].items['README.md'].refresh_mark(None) == {
            "url": "https://downloads.sourceforge.net/project/checkstyle.mirror/checkstyle-10.9.0/README.md",
            "etag": "\"6413020d-2a9\"",
            "expires": None,
            "content_length": 681,
            "content_type": "application/octet-stream"
        }
        assert tree.items['checkstyle-10.9.0'].items['checkstyle-10.9.0-all.jar'].refresh_mark(None) == {
            "url": "https://downloads.sourceforge.net/project/"
                   "checkstyle.mirror/checkstyle-10.9.0/checkstyle-10.9.0-all.jar",
            "etag": "\"64130497-fe8110\"",
            "expires": None,
            "content_length": 16679184,
            "content_type": "application/java-archive"
        }

    def test_native(self):
        resource = SourceForgeFilesResource('checkstyle.mirror')
        tree = resource.sync_tree()
        print(tree.items)
        assert 'LATEST_RELEASE' not in tree.items
        assert 'LATEST_RELEASE_10' not in tree.items
        assert 'LATEST_RELEASE_10.9.0' not in tree.items
        assert 'LATEST_RELEASE_10.9.1' not in tree.items
        assert 'LATEST_RELEASE_10.9.2' not in tree.items
        assert 'LATEST_RELEASE_10.9.3' not in tree.items

        assert tree.items['checkstyle-10.9.0'].items['README.md'].refresh_mark(None) == {
            "url": "https://downloads.sourceforge.net/project/checkstyle.mirror/checkstyle-10.9.0/README.md",
            "etag": "\"6413020d-2a9\"",
            "expires": None,
            "content_length": 681,
            "content_type": "application/octet-stream"
        }
        assert tree.items['checkstyle-10.9.0'].items['checkstyle-10.9.0-all.jar'].refresh_mark(None) == {
            "url": "https://downloads.sourceforge.net/project/"
                   "checkstyle.mirror/checkstyle-10.9.0/checkstyle-10.9.0-all.jar",
            "etag": "\"64130497-fe8110\"",
            "expires": None,
            "content_length": 16679184,
            "content_type": "application/java-archive"
        }
