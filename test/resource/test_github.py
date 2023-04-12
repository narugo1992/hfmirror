import pytest
from hbutils.testing import disable_output

from hfmirror.resource import GithubReleaseResource


@pytest.fixture(scope='module')
def narugo1992_gchar(github_client):
    return GithubReleaseResource(
        repo='narugo1992/gchar',
        github_client=github_client,
        add_version_attachment=True,
    )


@pytest.fixture(scope='module')
def narugo1992_gchar_tree(narugo1992_gchar):
    with disable_output():
        return narugo1992_gchar.sync_tree()


class CustomGithubResource(GithubReleaseResource):
    def _tag_filter(self, tag):
        if tag >= 'v0.0.2':
            return None
        return tag

    def _filename_filter(self, tag, filename):
        if tag >= 'v0.0.2' or not filename.endswith('.whl'):
            return None
        return filename


@pytest.fixture(scope='module')
def custom_gchar(github_client):
    return CustomGithubResource(
        repo='narugo1992/gchar',
        github_client=github_client,
        add_version_attachment=True,
    )


@pytest.fixture(scope='module')
def custom_gchar_tree(custom_gchar):
    with disable_output():
        return custom_gchar.sync_tree()


@pytest.mark.unittest
class TestResourceGithub:
    def test_basic_usage(self, narugo1992_gchar, narugo1992_gchar_tree):
        assert narugo1992_gchar.repo == 'narugo1992/gchar'
        assert narugo1992_gchar.add_version_attachment

        assert narugo1992_gchar_tree.metadata == {}
        assert narugo1992_gchar_tree.items['v0.0.6'].metadata == {
            "version": "v0.0.6",
            "title": "v0.0.6",
            "url": "https://github.com/narugo1992/gchar/releases/tag/v0.0.6",
        }
        assert 'gchar-0.0.6.tar.gz' in narugo1992_gchar_tree.items['v0.0.6'].items
        assert 'gchar-0.0.6-py3-none-any.whl' in narugo1992_gchar_tree.items['v0.0.6'].items

    def test_init_warn(self, github_client, github_access_token):
        with pytest.warns(Warning):
            GithubReleaseResource('narugo1992/gchar', github_client=github_client, access_token=github_access_token)

    def test_custom_usage(self, custom_gchar, custom_gchar_tree):
        assert custom_gchar.repo == 'narugo1992/gchar'
        assert custom_gchar.add_version_attachment

        assert custom_gchar_tree.metadata == {}
        assert 'v0.0.6' not in custom_gchar_tree.items
        assert 'v0.0.2' not in custom_gchar_tree.items
        assert custom_gchar_tree.items['v0.0.1'].metadata == {
            "version": "v0.0.1",
            "title": "v0.0.1",
            "url": "https://github.com/narugo1992/gchar/releases/tag/v0.0.1",
        }
        assert 'gchar-0.0.1.tar.gz' not in custom_gchar_tree.items['v0.0.1'].items
        assert 'gchar-0.0.1-py3-none-any.whl' in custom_gchar_tree.items['v0.0.1'].items
