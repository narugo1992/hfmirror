import os.path

import pytest
import requests

from .testfile import isolated_to_testfile


@pytest.mark.unittest
class TestTestingTestfile:
    @isolated_to_testfile()
    def test_isolated_to_testfile(self):
        assert os.path.exists('.keep')

    def test_url_to_testfile(self, url_to_testfile, url_to_game_characters):
        assert requests.get(url_to_testfile).status_code == 200
        assert requests.get(f'{url_to_testfile}/.keep').status_code == 200
        assert requests.get(f'{url_to_testfile}/_this_file_should_not_exist').status_code == 404
