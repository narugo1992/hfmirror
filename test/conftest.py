import os
import re

import pytest
from github import Github
from hbutils.random import random_sha1_with_timestamp
from hbutils.testing import TextAligner
from huggingface_hub import HfApi

from .testing import start_http_server_to_testfile


@pytest.fixture()
def text_align():
    return TextAligner().multiple_lines()


@pytest.fixture(scope='session')
def url_to_testfile():
    with start_http_server_to_testfile() as url:
        yield url


@pytest.fixture(scope='session')
def url_to_game_characters():
    yield 'https://huggingface.co/datasets/deepghs/game_characters/resolve/main'


@pytest.fixture(scope='session')
def url_to_game_character_skins():
    yield 'https://huggingface.co/datasets/deepghs/game_character_skins/resolve/main'


@pytest.fixture(scope='session')
def github_access_token():
    return os.environ.get('GH_ACCESS_TOKEN')


@pytest.fixture(scope='session')
def github_client(github_access_token) -> Github:
    yield Github(github_access_token)


@pytest.fixture(scope='session')
def huggingface_access_token():
    return os.environ.get('HF_TOKEN')


@pytest.fixture(scope='session')
def huggingface_client(huggingface_access_token):
    return HfApi(token=huggingface_access_token)


_REPO_URL_PATTERN = re.compile(r'^https://huggingface.co/datasets/(?P<repo>[a-zA-Z\d/_\-]+)$')


@pytest.fixture()
def huggingface_repo(huggingface_client):
    repo_name = f'test_repo_{random_sha1_with_timestamp()}'
    url = huggingface_client.create_repo(repo_name, repo_type='dataset', exist_ok=True)
    repo_name = _REPO_URL_PATTERN.fullmatch(url).group('repo')
    try:
        yield repo_name
    finally:
        huggingface_client.delete_repo(repo_name, repo_type='dataset')
