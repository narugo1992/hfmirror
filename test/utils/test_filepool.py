import json
import os.path

import pytest
from hbutils.system import TemporaryDirectory
from hbutils.testing import isolated_directory

from hfmirror.utils.filepool import FilePool


@pytest.mark.unittest
class TestUtilsFilepool:
    def test_filepool(self):
        fp = FilePool()
        assert len(fp) == 0

        with TemporaryDirectory() as td:
            file = os.path.join(td, '111.json')
            with open(file, 'w', encoding='utf-8') as f:
                json.dump({'a': 1, 'b': 3, 'apb': 4}, f, sort_keys=True)

            f1 = fp.put_file(file)

        with isolated_directory():
            file = 'dksj.json'
            with open(file, 'w', encoding='utf-8') as f:
                json.dump({'a': 12, 'b': 36, 'apb': 48}, f, sort_keys=True)

            f2 = fp.put_file(file)

        with open(f1, 'r', encoding='utf-8') as f:
            assert json.load(f) == {'a': 1, 'b': 3, 'apb': 4}
        with open(f2, 'r', encoding='utf-8') as f:
            assert json.load(f) == {'a': 12, 'b': 36, 'apb': 48}
        assert len(fp) == 2

    def test_filepool_with_cleanup(self):
        fp = FilePool()
        assert len(fp) == 0

        with TemporaryDirectory() as td:
            file = os.path.join(td, '111.json')
            with open(file, 'w', encoding='utf-8') as f:
                json.dump({'a': 1, 'b': 3, 'apb': 4}, f, sort_keys=True)

            f1 = fp.put_file(file)

        with open(f1, 'r', encoding='utf-8') as f:
            assert json.load(f) == {'a': 1, 'b': 3, 'apb': 4}
        assert len(fp) == 1

        fp.cleanup()
        assert len(fp) == 0
        with isolated_directory():
            file = 'dksj.json'
            with open(file, 'w', encoding='utf-8') as f:
                json.dump({'a': 12, 'b': 36, 'apb': 48}, f, sort_keys=True)

            f2 = fp.put_file(file)

        assert not os.path.exists(f1)
        with open(f2, 'r', encoding='utf-8') as f:
            assert json.load(f) == {'a': 12, 'b': 36, 'apb': 48}
        assert len(fp) == 1

        fp.cleanup()
        assert not os.path.exists(f2)
        assert len(fp) == 0
