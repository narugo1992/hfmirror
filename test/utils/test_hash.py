import pytest

from hfmirror.utils import hash_anything


@pytest.mark.unittest
class TestUtilsHash:
    def test_hash_anything(self):
        assert hash_anything(1) == hash(1)
        assert hash_anything('lkdfjglkdflg') == hash('lkdfjglkdflg')
        assert hash_anything(int) == hash(int)

        assert hash_anything([1, 2, 'ds']) == hash((list, (1, 2, 'ds')))
        assert hash_anything({'b': 2, 'a': 3, 333: [1, 2, 'ds']}) == \
               hash((dict, (('a', 3), ('b', 2), (333, (list, (1, 2, 'ds'))))))
