# Task 1.2: RepositoryProvider — Implementation Guide

## Поточний стан

`github.py` — `GitHubClient(GitProvider)` з PyGithub.
`gitlab.py` — `GitLabClient(GitProvider)` з python-gitlab.

Обидва мають `self.github` / `self.gitlab` об'єкти, через які можна
звертатись до Repository API вже зараз.

---

## Що створити

### 1. `src/ai_reviewer/integrations/repository.py`

```python
from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel, ConfigDict


class RepositoryMetadata(BaseModel):
    """Метадані з Platform API."""
    model_config = ConfigDict(frozen=True)

    name: str
    description: str | None = None
    default_branch: str = "main"
    topics: tuple[str, ...] = ()
    license: str | None = None
    visibility: str = "private"
    ci_config_path: str | None = None         # GitLab: custom CI path


class RepositoryProvider(ABC):
    """Доступ до репозиторію — окремо від MR-операцій."""

    @abstractmethod
    def get_languages(self, repo_name: str) -> dict[str, float]:
        """Мови проєкту. {name: percentage}.

        GitHub: repo.get_languages() → bytes → convert to %.
        GitLab: project.languages.get() → already %.
        """

    @abstractmethod
    def get_metadata(self, repo_name: str) -> RepositoryMetadata:
        """Базові метадані."""

    @abstractmethod
    def get_file_tree(
        self,
        repo_name: str,
        *,
        ref: str | None = None,
    ) -> tuple[str, ...]:
        """Список файлів (шляхи). Без клонування.

        Ліміт: max 10 000 entries (GitHub API ліміт для recursive tree).
        """

    @abstractmethod
    def get_file_content(
        self,
        repo_name: str,
        path: str,
        *,
        ref: str | None = None,
    ) -> str | None:
        """Вміст файлу як string. None якщо binary або не існує."""
```

### 2. Розширити `GitHubClient`

```python
# github.py

from ai_reviewer.integrations.repository import RepositoryProvider, RepositoryMetadata


class GitHubClient(GitProvider, RepositoryProvider):

    @with_retry
    def get_languages(self, repo_name: str) -> dict[str, float]:
        try:
            repo = self._github.get_repo(repo_name)
            langs = repo.get_languages()  # {name: bytes}
            total = sum(langs.values())
            if total == 0:
                return {}
            return {name: round(bytes_ / total * 100, 1) for name, bytes_ in langs.items()}
        except GithubException as e:
            raise _convert_github_exception(e) from e

    @with_retry
    def get_metadata(self, repo_name: str) -> RepositoryMetadata:
        try:
            repo = self._github.get_repo(repo_name)
            return RepositoryMetadata(
                name=repo.full_name,
                description=repo.description,
                default_branch=repo.default_branch,
                topics=tuple(repo.get_topics()),
                license=repo.license.spdx_id if repo.license else None,
                visibility="public" if not repo.private else "private",
            )
        except GithubException as e:
            raise _convert_github_exception(e) from e

    @with_retry
    def get_file_tree(self, repo_name: str, *, ref: str | None = None) -> tuple[str, ...]:
        try:
            repo = self._github.get_repo(repo_name)
            branch = ref or repo.default_branch
            tree = repo.get_git_tree(branch, recursive=True)
            # tree.tree is list of GitTreeElement, filter blobs only
            return tuple(
                item.path for item in tree.tree
                if item.type == "blob"
            )
        except GithubException as e:
            raise _convert_github_exception(e) from e

    @with_retry
    def get_file_content(
        self, repo_name: str, path: str, *, ref: str | None = None,
    ) -> str | None:
        try:
            repo = self._github.get_repo(repo_name)
            kwargs = {"ref": ref} if ref else {}
            content_file = repo.get_contents(path, **kwargs)
            if isinstance(content_file, list):
                return None  # це директорія
            try:
                return content_file.decoded_content.decode("utf-8")
            except UnicodeDecodeError:
                return None  # binary file
        except GithubException as e:
            if getattr(e, "status", None) == 404:
                return None
            raise _convert_github_exception(e) from e
```

### 3. Розширити `GitLabClient`

```python
# gitlab.py

class GitLabClient(GitProvider, RepositoryProvider):

    @with_retry
    def get_languages(self, repo_name: str) -> dict[str, float]:
        try:
            project = self.gitlab.projects.get(repo_name)
            return dict(project.languages())  # already {name: percentage}
        except GitlabError as e:
            raise _convert_gitlab_exception(e) from e

    @with_retry
    def get_metadata(self, repo_name: str) -> RepositoryMetadata:
        try:
            project = self.gitlab.projects.get(repo_name)
            return RepositoryMetadata(
                name=project.path_with_namespace,
                description=project.description,
                default_branch=project.default_branch,
                topics=tuple(project.topics or []),
                license=None,  # GitLab: project.license → needs separate call
                visibility=project.visibility,
                ci_config_path=getattr(project, "ci_config_path", None),
            )
        except GitlabError as e:
            raise _convert_gitlab_exception(e) from e

    @with_retry
    def get_file_tree(self, repo_name: str, *, ref: str | None = None) -> tuple[str, ...]:
        try:
            project = self.gitlab.projects.get(repo_name)
            kwargs = {"ref": ref} if ref else {}
            items = project.repository_tree(
                recursive=True, all=True, per_page=100, **kwargs,
            )
            return tuple(
                item["path"] for item in items
                if item["type"] == "blob"
            )
        except GitlabError as e:
            raise _convert_gitlab_exception(e) from e

    @with_retry
    def get_file_content(
        self, repo_name: str, path: str, *, ref: str | None = None,
    ) -> str | None:
        try:
            project = self.gitlab.projects.get(repo_name)
            kwargs = {"ref": ref or project.default_branch}
            f = project.files.get(path, **kwargs)
            try:
                return f.decode().decode("utf-8")
            except UnicodeDecodeError:
                return None
        except GitlabError as e:
            if getattr(e, "response_code", None) == 404:
                return None
            raise _convert_gitlab_exception(e) from e
```

---

## Тести

### `tests/unit/test_repository_provider.py`

- Mock `Github()` / `gitlab.Gitlab()` objects
- `get_languages()` — conversion bytes→%, empty repo
- `get_metadata()` — all fields populated, optional fields None
- `get_file_tree()` — filter blobs only, large repos
- `get_file_content()` — text file, binary file (returns None), 404 (returns None)
- Error conversion: platform errors → custom hierarchy

---

## Чеклист

- [ ] `integrations/repository.py` — ABC + RepositoryMetadata
- [ ] `GitHubClient` extends `RepositoryProvider` — 4 methods
- [ ] `GitLabClient` extends `RepositoryProvider` — 4 methods
- [ ] Unit-тести для обох платформ
- [ ] `make check` проходить
