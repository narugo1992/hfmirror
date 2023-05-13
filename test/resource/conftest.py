import pytest


class _Anything:
    def __eq__(self, other):
        return True


@pytest.fixture()
def etag_anything():
    return _Anything()
