"""Unit tests for RepositoryProvider ABC, RepositoryMetadata, and implementations."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest
from github import GithubException, RateLimitExceededException
from gitlab.exceptions import GitlabError
from pydantic import ValidationError

from ai_reviewer.integrations.github import GitHubClient
from ai_reviewer.integrations.gitlab import GitLabClient
from ai_reviewer.integrations.repository import RepositoryMetadata, RepositoryProvider
from ai_reviewer.utils.retry import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ServerError,
)

if TYPE_CHECKING:
    from unittest.mock import MagicMock


# ── RepositoryMetadata model tests ─────────────────────────────────


class TestRepositoryMetadata:
    """Tests for RepositoryMetadata Pydantic model."""

    def test_create_minimal(self) -> None:
        """Test creating metadata with only required fields."""
        meta = RepositoryMetadata(name="owner/repo")
        assert meta.name == "owner/repo"
        assert meta.description is None
        assert meta.default_branch == "main"
        assert meta.topics == ()
        assert meta.license is None
        assert meta.visibility == "private"
        assert meta.ci_config_path is None

    def test_create_full(self) -> None:
        """Test creating metadata with all fields."""
        meta = RepositoryMetadata(
            name="owner/repo",
            description="A test repo",
            default_branch="develop",
            topics=("python", "testing"),
            license="MIT",
            visibility="public",
            ci_config_path=".gitlab-ci.yml",
        )
        assert meta.name == "owner/repo"
        assert meta.description == "A test repo"
        assert meta.default_branch == "develop"
        assert meta.topics == ("python", "testing")
        assert meta.license == "MIT"
        assert meta.visibility == "public"
        assert meta.ci_config_path == ".gitlab-ci.yml"

    def test_frozen(self) -> None:
        """Test that RepositoryMetadata is immutable."""
        meta = RepositoryMetadata(name="owner/repo")
        with pytest.raises(ValidationError):
            meta.name = "other/repo"  # type: ignore[misc]

    def test_empty_name_rejected(self) -> None:
        """Test that empty name is rejected (min_length=1)."""
        with pytest.raises(ValidationError):
            RepositoryMetadata(name="")

    def test_serialization_roundtrip(self) -> None:
        """Test JSON serialization and deserialization."""
        meta = RepositoryMetadata(
            name="owner/repo",
            description="desc",
            topics=("a", "b"),
            license="Apache-2.0",
        )
        data = meta.model_dump()
        restored = RepositoryMetadata(**data)
        assert restored == meta

    def test_invalid_visibility_rejected(self) -> None:
        """Test that invalid visibility value is rejected by Literal."""
        with pytest.raises(ValidationError):
            RepositoryMetadata(name="owner/repo", visibility="archived")  # type: ignore[arg-type]

    def test_internal_visibility_accepted(self) -> None:
        """Test that 'internal' visibility is valid (GitLab-specific)."""
        meta = RepositoryMetadata(name="owner/repo", visibility="internal")
        assert meta.visibility == "internal"


# ── RepositoryProvider ABC tests ───────────────────────────────────


class TestRepositoryProviderABC:
    """Tests for the RepositoryProvider abstract base class."""

    def test_cannot_instantiate(self) -> None:
        """Test that RepositoryProvider cannot be instantiated directly."""
        with pytest.raises(TypeError, match="abstract"):
            RepositoryProvider()  # type: ignore[abstract]

    def test_incomplete_subclass(self) -> None:
        """Test that a subclass missing methods cannot be instantiated."""

        class _Incomplete(RepositoryProvider):
            def get_languages(self, repo_name: str) -> dict[str, float]:
                return {}

        with pytest.raises(TypeError, match="abstract"):
            _Incomplete()  # type: ignore[abstract]

    def test_github_implements_interface(self) -> None:
        """Test that GitHubClient implements RepositoryProvider."""
        with patch("ai_reviewer.integrations.github.Github"):
            client = GitHubClient("token")
        assert isinstance(client, RepositoryProvider)

    def test_gitlab_implements_interface(self) -> None:
        """Test that GitLabClient implements RepositoryProvider."""
        with patch("ai_reviewer.integrations.gitlab.gitlab.Gitlab"):
            client = GitLabClient("token")
        assert isinstance(client, RepositoryProvider)


# ── GitHub RepositoryProvider tests ────────────────────────────────


class TestGitHubRepositoryProvider:
    """Tests for GitHubClient RepositoryProvider methods."""

    @pytest.fixture
    def mock_github(self) -> MagicMock:
        """Mock PyGithub instance."""
        with patch("ai_reviewer.integrations.github.Github") as mock:
            yield mock

    @pytest.fixture
    def client(self, mock_github: MagicMock) -> GitHubClient:
        """Create GitHubClient instance with mocked Github."""
        return GitHubClient("test-token")

    # ── get_languages ──────────────────────────────────────────────

    def test_get_languages_converts_bytes_to_percentages(self, client: GitHubClient) -> None:
        """Test that bytes are converted to percentages."""
        mock_repo = Mock()
        client.github.get_repo.return_value = mock_repo
        mock_repo.get_languages.return_value = {"Python": 7000, "JavaScript": 3000}

        result = client.get_languages("owner/repo")

        assert result == {"Python": 70.0, "JavaScript": 30.0}

    def test_get_languages_empty_repo(self, client: GitHubClient) -> None:
        """Test empty repo returns empty dict."""
        mock_repo = Mock()
        client.github.get_repo.return_value = mock_repo
        mock_repo.get_languages.return_value = {}

        result = client.get_languages("owner/repo")

        assert result == {}

    def test_get_languages_single_language(self, client: GitHubClient) -> None:
        """Test single language returns 100%."""
        mock_repo = Mock()
        client.github.get_repo.return_value = mock_repo
        mock_repo.get_languages.return_value = {"Python": 5000}

        result = client.get_languages("owner/repo")

        assert result == {"Python": 100.0}

    @pytest.mark.slow
    def test_get_languages_rate_limit(self, client: GitHubClient) -> None:
        """Test rate limit raises RateLimitError."""
        client.github.get_repo.side_effect = RateLimitExceededException(
            403, {"message": "rate limit"}, {}
        )

        with pytest.raises(RateLimitError):
            client.get_languages("owner/repo")

    def test_get_languages_github_error(self, client: GitHubClient) -> None:
        """Test GithubException is converted."""
        client.github.get_repo.side_effect = GithubException(
            401, {"message": "Bad credentials"}, {}
        )

        with pytest.raises(AuthenticationError):
            client.get_languages("owner/repo")

    # ── get_metadata ───────────────────────────────────────────────

    def test_get_metadata_success(self, client: GitHubClient) -> None:
        """Test successful metadata retrieval."""
        mock_repo = Mock()
        client.github.get_repo.return_value = mock_repo
        mock_repo.full_name = "owner/repo"
        mock_repo.description = "A cool repo"
        mock_repo.default_branch = "main"
        mock_repo.get_topics.return_value = ["python", "ci"]
        mock_repo.license = Mock()
        mock_repo.license.spdx_id = "MIT"
        mock_repo.private = False

        result = client.get_metadata("owner/repo")

        assert isinstance(result, RepositoryMetadata)
        assert result.name == "owner/repo"
        assert result.description == "A cool repo"
        assert result.default_branch == "main"
        assert result.topics == ("python", "ci")
        assert result.license == "MIT"
        assert result.visibility == "public"
        assert result.ci_config_path is None

    def test_get_metadata_no_license(self, client: GitHubClient) -> None:
        """Test metadata with no license."""
        mock_repo = Mock()
        client.github.get_repo.return_value = mock_repo
        mock_repo.full_name = "owner/repo"
        mock_repo.description = None
        mock_repo.default_branch = "main"
        mock_repo.get_topics.return_value = []
        mock_repo.license = None
        mock_repo.private = True

        result = client.get_metadata("owner/repo")

        assert result.license is None
        assert result.visibility == "private"
        assert result.description is None

    @pytest.mark.slow
    def test_get_metadata_rate_limit(self, client: GitHubClient) -> None:
        """Test rate limit raises RateLimitError."""
        client.github.get_repo.side_effect = RateLimitExceededException(
            403, {"message": "rate limit"}, {}
        )

        with pytest.raises(RateLimitError):
            client.get_metadata("owner/repo")

    # ── get_file_tree ──────────────────────────────────────────────

    def test_get_file_tree_blobs_only(self, client: GitHubClient) -> None:
        """Test that only blobs are returned (no trees)."""
        mock_repo = Mock()
        client.github.get_repo.return_value = mock_repo
        mock_repo.default_branch = "main"

        blob1 = Mock(path="src/main.py", type="blob")
        blob2 = Mock(path="README.md", type="blob")
        tree_item = Mock(path="src", type="tree")

        mock_tree = Mock()
        mock_tree.tree = [blob1, tree_item, blob2]
        mock_repo.get_git_tree.return_value = mock_tree

        result = client.get_file_tree("owner/repo")

        assert result == ("src/main.py", "README.md")
        mock_repo.get_git_tree.assert_called_once_with("main", recursive=True)

    def test_get_file_tree_custom_ref(self, client: GitHubClient) -> None:
        """Test file tree with custom ref."""
        mock_repo = Mock()
        client.github.get_repo.return_value = mock_repo

        mock_tree = Mock()
        mock_tree.tree = [Mock(path="file.py", type="blob")]
        mock_repo.get_git_tree.return_value = mock_tree

        result = client.get_file_tree("owner/repo", ref="develop")

        assert result == ("file.py",)
        mock_repo.get_git_tree.assert_called_once_with("develop", recursive=True)

    def test_get_file_tree_empty(self, client: GitHubClient) -> None:
        """Test empty file tree."""
        mock_repo = Mock()
        client.github.get_repo.return_value = mock_repo
        mock_repo.default_branch = "main"

        mock_tree = Mock()
        mock_tree.tree = []
        mock_repo.get_git_tree.return_value = mock_tree

        result = client.get_file_tree("owner/repo")

        assert result == ()

    def test_get_file_tree_truncated_logs_warning(
        self, client: GitHubClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that truncated tree logs a warning."""
        mock_repo = Mock()
        client.github.get_repo.return_value = mock_repo
        mock_repo.default_branch = "main"

        mock_tree = Mock()
        mock_tree.truncated = True
        mock_tree.tree = [Mock(path="file.py", type="blob")]
        mock_repo.get_git_tree.return_value = mock_tree

        result = client.get_file_tree("owner/repo")

        assert result == ("file.py",)
        assert "truncated" in caplog.text

    def test_get_file_tree_github_error(self, client: GitHubClient) -> None:
        """Test GithubException is converted."""
        client.github.get_repo.side_effect = GithubException(404, {"message": "Not Found"}, {})

        with pytest.raises(NotFoundError):
            client.get_file_tree("owner/repo")

    # ── get_file_content ───────────────────────────────────────────

    def test_get_file_content_text(self, client: GitHubClient) -> None:
        """Test reading a text file."""
        mock_repo = Mock()
        client.github.get_repo.return_value = mock_repo

        mock_content = Mock()
        mock_content.type = "file"
        mock_content.decoded_content = b"print('hello')"
        mock_repo.get_contents.return_value = mock_content

        result = client.get_file_content("owner/repo", "main.py")

        assert result == "print('hello')"

    def test_get_file_content_with_ref(self, client: GitHubClient) -> None:
        """Test reading a file with specific ref."""
        mock_repo = Mock()
        client.github.get_repo.return_value = mock_repo

        mock_content = Mock()
        mock_content.type = "file"
        mock_content.decoded_content = b"v2"
        mock_repo.get_contents.return_value = mock_content

        result = client.get_file_content("owner/repo", "file.py", ref="v2-branch")

        assert result == "v2"
        mock_repo.get_contents.assert_called_once_with("file.py", ref="v2-branch")

    def test_get_file_content_binary_returns_none(self, client: GitHubClient) -> None:
        """Test that binary files return None."""
        mock_repo = Mock()
        client.github.get_repo.return_value = mock_repo

        mock_content = Mock()
        mock_content.type = "file"
        # Use a Mock with decode that raises, since real bytes.decode is read-only
        mock_decoded = Mock()
        mock_decoded.decode.side_effect = UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")
        mock_content.decoded_content = mock_decoded
        mock_repo.get_contents.return_value = mock_content

        result = client.get_file_content("owner/repo", "image.png")

        assert result is None

    def test_get_file_content_not_found_returns_none(self, client: GitHubClient) -> None:
        """Test that 404 returns None instead of raising."""
        mock_repo = Mock()
        client.github.get_repo.return_value = mock_repo
        mock_repo.get_contents.side_effect = GithubException(404, {"message": "Not Found"}, {})

        result = client.get_file_content("owner/repo", "missing.py")

        assert result is None

    def test_get_file_content_directory_returns_none(self, client: GitHubClient) -> None:
        """Test that a directory path returns None."""
        mock_repo = Mock()
        client.github.get_repo.return_value = mock_repo
        # GitHub API returns a list for directories
        mock_repo.get_contents.return_value = [Mock(), Mock()]

        result = client.get_file_content("owner/repo", "src/")

        assert result is None

    def test_get_file_content_submodule_returns_none(self, client: GitHubClient) -> None:
        """Test that a submodule returns None."""
        mock_repo = Mock()
        client.github.get_repo.return_value = mock_repo

        mock_content = Mock()
        mock_content.type = "submodule"
        mock_repo.get_contents.return_value = mock_content

        result = client.get_file_content("owner/repo", "vendor/lib")

        assert result is None

    def test_get_file_content_symlink_returns_none(self, client: GitHubClient) -> None:
        """Test that a symlink returns None."""
        mock_repo = Mock()
        client.github.get_repo.return_value = mock_repo

        mock_content = Mock()
        mock_content.type = "symlink"
        mock_repo.get_contents.return_value = mock_content

        result = client.get_file_content("owner/repo", "link.py")

        assert result is None

    @pytest.mark.slow
    def test_get_file_content_server_error(self, client: GitHubClient) -> None:
        """Test that 500 raises ServerError."""
        mock_repo = Mock()
        client.github.get_repo.return_value = mock_repo
        mock_repo.get_contents.side_effect = GithubException(
            500, {"message": "Internal Server Error"}, {}
        )

        with pytest.raises(ServerError):
            client.get_file_content("owner/repo", "file.py")


# ── GitLab RepositoryProvider tests ────────────────────────────────


class TestGitLabRepositoryProvider:
    """Tests for GitLabClient RepositoryProvider methods."""

    @pytest.fixture
    def mock_gitlab(self) -> MagicMock:
        """Mock python-gitlab instance."""
        with patch("ai_reviewer.integrations.gitlab.gitlab.Gitlab") as mock:
            yield mock

    @pytest.fixture
    def client(self, mock_gitlab: MagicMock) -> GitLabClient:
        """Create GitLabClient instance with mocked Gitlab."""
        return GitLabClient("test-token", "https://gitlab.example.com")

    # ── get_languages ──────────────────────────────────────────────

    def test_get_languages_returns_percentages(self, client: GitLabClient) -> None:
        """Test that GitLab percentages are returned as-is."""
        mock_project = Mock()
        client.gitlab.projects.get.return_value = mock_project
        mock_project.languages.return_value = {"Python": 75.5, "Shell": 24.5}

        result = client.get_languages("group/repo")

        assert result == {"Python": 75.5, "Shell": 24.5}

    def test_get_languages_empty(self, client: GitLabClient) -> None:
        """Test empty languages dict."""
        mock_project = Mock()
        client.gitlab.projects.get.return_value = mock_project
        mock_project.languages.return_value = {}

        result = client.get_languages("group/repo")

        assert result == {}

    def test_get_languages_gitlab_error(self, client: GitLabClient) -> None:
        """Test GitlabError is converted."""
        error = GitlabError("Auth failed")
        error.response_code = 401
        client.gitlab.projects.get.side_effect = error

        with pytest.raises(AuthenticationError):
            client.get_languages("group/repo")

    # ── get_metadata ───────────────────────────────────────────────

    def test_get_metadata_success(self, client: GitLabClient) -> None:
        """Test successful metadata retrieval with GitLab-specific fields."""
        mock_project = Mock()
        client.gitlab.projects.get.return_value = mock_project
        mock_project.path_with_namespace = "group/repo"
        mock_project.description = "GitLab repo"
        mock_project.default_branch = "main"
        mock_project.topics = ["python", "gitlab"]
        mock_project.visibility = "internal"
        mock_project.ci_config_path = ".ci/pipeline.yml"

        result = client.get_metadata("group/repo")

        assert isinstance(result, RepositoryMetadata)
        assert result.name == "group/repo"
        assert result.description == "GitLab repo"
        assert result.default_branch == "main"
        assert result.topics == ("python", "gitlab")
        assert result.license is None  # GitLab requires separate API call
        assert result.visibility == "internal"
        assert result.ci_config_path == ".ci/pipeline.yml"

    def test_get_metadata_no_topics(self, client: GitLabClient) -> None:
        """Test metadata with no topics."""
        mock_project = Mock()
        client.gitlab.projects.get.return_value = mock_project
        mock_project.path_with_namespace = "group/repo"
        mock_project.description = None
        mock_project.default_branch = "develop"
        mock_project.topics = None
        mock_project.visibility = "private"
        mock_project.ci_config_path = None

        result = client.get_metadata("group/repo")

        assert result.topics == ()
        assert result.description is None

    @pytest.mark.slow
    def test_get_metadata_gitlab_error(self, client: GitLabClient) -> None:
        """Test GitlabError is converted."""
        error = GitlabError("Server error")
        error.response_code = 500
        client.gitlab.projects.get.side_effect = error

        with pytest.raises(ServerError):
            client.get_metadata("group/repo")

    # ── get_file_tree ──────────────────────────────────────────────

    def test_get_file_tree_blobs_only(self, client: GitLabClient) -> None:
        """Test that only blobs are returned."""
        mock_project = Mock()
        client.gitlab.projects.get.return_value = mock_project
        mock_project.repository_tree.return_value = [
            {"path": "src/main.py", "type": "blob"},
            {"path": "src", "type": "tree"},
            {"path": "README.md", "type": "blob"},
        ]

        result = client.get_file_tree("group/repo")

        assert result == ("src/main.py", "README.md")
        mock_project.repository_tree.assert_called_once_with(
            recursive=True,
            get_all=True,
            per_page=100,
        )

    def test_get_file_tree_custom_ref(self, client: GitLabClient) -> None:
        """Test file tree with custom ref."""
        mock_project = Mock()
        client.gitlab.projects.get.return_value = mock_project
        mock_project.repository_tree.return_value = [
            {"path": "file.py", "type": "blob"},
        ]

        result = client.get_file_tree("group/repo", ref="v1.0.0")

        assert result == ("file.py",)
        mock_project.repository_tree.assert_called_once_with(
            recursive=True,
            get_all=True,
            per_page=100,
            ref="v1.0.0",
        )

    def test_get_file_tree_empty(self, client: GitLabClient) -> None:
        """Test empty file tree."""
        mock_project = Mock()
        client.gitlab.projects.get.return_value = mock_project
        mock_project.repository_tree.return_value = []

        result = client.get_file_tree("group/repo")

        assert result == ()

    def test_get_file_tree_gitlab_error(self, client: GitLabClient) -> None:
        """Test GitlabError is converted."""
        error = GitlabError("Not Found")
        error.response_code = 404
        client.gitlab.projects.get.side_effect = error

        with pytest.raises(NotFoundError):
            client.get_file_tree("group/repo")

    # ── get_file_content ───────────────────────────────────────────

    def test_get_file_content_text(self, client: GitLabClient) -> None:
        """Test reading a text file."""
        mock_project = Mock()
        client.gitlab.projects.get.return_value = mock_project
        mock_project.default_branch = "main"

        mock_file = Mock()
        mock_file.decode.return_value = b"print('hello')"
        mock_project.files.get.return_value = mock_file

        result = client.get_file_content("group/repo", "main.py")

        assert result == "print('hello')"
        mock_project.files.get.assert_called_once_with("main.py", ref="main")

    def test_get_file_content_with_ref(self, client: GitLabClient) -> None:
        """Test reading a file with specific ref."""
        mock_project = Mock()
        client.gitlab.projects.get.return_value = mock_project

        mock_file = Mock()
        mock_file.decode.return_value = b"v2 content"
        mock_project.files.get.return_value = mock_file

        result = client.get_file_content("group/repo", "file.py", ref="develop")

        assert result == "v2 content"
        mock_project.files.get.assert_called_once_with("file.py", ref="develop")

    def test_get_file_content_binary_returns_none(self, client: GitLabClient) -> None:
        """Test that binary files return None."""
        mock_project = Mock()
        client.gitlab.projects.get.return_value = mock_project
        mock_project.default_branch = "main"

        mock_file = Mock()
        # Use a Mock with decode that raises, since real bytes.decode is read-only
        mock_raw = Mock()
        mock_raw.decode.side_effect = UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")
        mock_file.decode.return_value = mock_raw
        mock_project.files.get.return_value = mock_file

        result = client.get_file_content("group/repo", "image.png")

        assert result is None

    def test_get_file_content_not_found_returns_none(self, client: GitLabClient) -> None:
        """Test that 404 returns None instead of raising."""
        mock_project = Mock()
        client.gitlab.projects.get.return_value = mock_project
        mock_project.default_branch = "main"

        error = GitlabError("Not Found")
        error.response_code = 404
        mock_project.files.get.side_effect = error

        result = client.get_file_content("group/repo", "missing.py")

        assert result is None

    @pytest.mark.slow
    def test_get_file_content_server_error(self, client: GitLabClient) -> None:
        """Test that 500 raises ServerError."""
        mock_project = Mock()
        client.gitlab.projects.get.return_value = mock_project
        mock_project.default_branch = "main"

        error = GitlabError("Internal Error")
        error.response_code = 500
        mock_project.files.get.side_effect = error

        with pytest.raises(ServerError):
            client.get_file_content("group/repo", "file.py")
