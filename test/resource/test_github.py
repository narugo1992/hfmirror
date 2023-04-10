import pytest

from hfmirror.resource import GithubReleaseResource


@pytest.fixture(scope='module')
def narugo1992_gchar(github_client):
    return GithubReleaseResource(
        repo='narugo1992/gchar',
        github=github_client,
        add_version_attachment=True,
    )


@pytest.mark.unittest
class TestResourceGithub:
    def test_basic_usage(self, narugo1992_gchar):
        pass
