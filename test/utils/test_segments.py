import pytest

from hfmirror.utils import to_segments


@pytest.mark.unittest
class TestUtilsSegments:
    def test_to_segments(self):
        assert to_segments(r'a/b/c') == ['a', 'b', 'c']
        assert to_segments(r'a\b\c') == ['a', 'b', 'c']
        assert to_segments(r'a/b/../c/./d/e//f/..') == ['a', 'c', 'd', 'e']
        assert to_segments(r'a\b\..\c\.\d\\e\f\\..') == ['a', 'c', 'd', 'e']
        assert to_segments(r'a/b/../c/./d/e//f/..'.split('/')) == ['a', 'c', 'd', 'e']
        assert to_segments(r'a\b\..\c\.\d\\e\f\\..'.split('\\')) == ['a', 'c', 'd', 'e']

        with pytest.raises(ValueError):
            to_segments('*/./?')
        with pytest.raises(ValueError):
            to_segments('con')

        assert to_segments('') == []
