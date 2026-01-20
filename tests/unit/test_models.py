"""Unit tests for core data models."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from ai_reviewer.core.models import (
    Comment,
    CommentAuthorType,
    FileChange,
    FileChangeType,
    LinkedTask,
    MergeRequest,
    ReviewContext,
    ReviewResult,
    TaskAlignmentStatus,
    Vulnerability,
    VulnerabilitySeverity,
)


class TestComment:
    """Tests for Comment model."""

    def test_create_minimal_comment(self) -> None:
        """Test creating a comment with minimal required fields."""
        comment = Comment(author="user1", body="LGTM")
        assert comment.author == "user1"
        assert comment.body == "LGTM"
        assert comment.author_type == CommentAuthorType.USER
        assert comment.created_at is None

    def test_create_full_comment(self) -> None:
        """Test creating a comment with all fields."""
        now = datetime.now(tz=UTC)
        comment = Comment(
            author="bot",
            author_type=CommentAuthorType.BOT,
            body="Automated review",
            created_at=now,
        )
        assert comment.author == "bot"
        assert comment.author_type == CommentAuthorType.BOT
        assert comment.body == "Automated review"
        assert comment.created_at == now

    def test_comment_author_required(self) -> None:
        """Test that author field is required."""
        with pytest.raises(ValidationError) as exc_info:
            Comment(body="test")  # type: ignore[call-arg]
        assert "author" in str(exc_info.value)

    def test_comment_author_not_empty(self) -> None:
        """Test that author cannot be empty."""
        with pytest.raises(ValidationError) as exc_info:
            Comment(author="", body="test")
        assert "author" in str(exc_info.value)

    def test_comment_is_frozen(self) -> None:
        """Test that comment model is immutable."""
        comment = Comment(author="user", body="test")
        with pytest.raises(ValidationError):
            comment.body = "modified"  # type: ignore[misc]

    def test_comment_created_at_must_be_timezone_aware(self) -> None:
        """Test that created_at rejects naive datetime."""
        naive_dt = datetime(2026, 1, 20, 12, 0, 0)  # noqa: DTZ001 - intentionally naive
        with pytest.raises(ValidationError) as exc_info:
            Comment(author="user", body="test", created_at=naive_dt)
        assert "timezone-aware" in str(exc_info.value)


class TestFileChange:
    """Tests for FileChange model."""

    def test_create_minimal_file_change(self) -> None:
        """Test creating a file change with minimal fields."""
        change = FileChange(filename="src/main.py", change_type=FileChangeType.MODIFIED)
        assert change.filename == "src/main.py"
        assert change.change_type == FileChangeType.MODIFIED
        assert change.additions == 0
        assert change.deletions == 0
        assert change.patch is None

    def test_create_full_file_change(self) -> None:
        """Test creating a file change with all fields."""
        change = FileChange(
            filename="src/new.py",
            change_type=FileChangeType.ADDED,
            additions=50,
            deletions=0,
            patch="@@ -0,0 +1,50 @@\n+# New file",
        )
        assert change.additions == 50
        assert change.patch is not None

    def test_renamed_file_change(self) -> None:
        """Test file change for renamed file."""
        change = FileChange(
            filename="src/new_name.py",
            change_type=FileChangeType.RENAMED,
            previous_filename="src/old_name.py",
        )
        assert change.change_type == FileChangeType.RENAMED
        assert change.previous_filename == "src/old_name.py"

    def test_filename_required(self) -> None:
        """Test that filename is required."""
        with pytest.raises(ValidationError):
            FileChange(change_type=FileChangeType.ADDED)  # type: ignore[call-arg]

    def test_filename_not_empty(self) -> None:
        """Test that filename cannot be empty."""
        with pytest.raises(ValidationError):
            FileChange(filename="", change_type=FileChangeType.ADDED)

    def test_additions_non_negative(self) -> None:
        """Test that additions must be non-negative."""
        with pytest.raises(ValidationError):
            FileChange(filename="test.py", change_type=FileChangeType.MODIFIED, additions=-1)

    def test_deletions_non_negative(self) -> None:
        """Test that deletions must be non-negative."""
        with pytest.raises(ValidationError):
            FileChange(filename="test.py", change_type=FileChangeType.MODIFIED, deletions=-5)

    def test_previous_filename_empty_string_becomes_none(self) -> None:
        """Test that empty previous_filename is converted to None."""
        change = FileChange(
            filename="test.py",
            change_type=FileChangeType.RENAMED,
            previous_filename="  ",
        )
        assert change.previous_filename is None


class TestMergeRequest:
    """Tests for MergeRequest model."""

    @pytest.fixture
    def minimal_mr(self) -> MergeRequest:
        """Create a minimal merge request for testing."""
        return MergeRequest(
            number=1,
            title="Add new feature",
            author="developer",
            source_branch="feature/new",
            target_branch="main",
        )

    @pytest.fixture
    def full_mr(self) -> MergeRequest:
        """Create a full merge request with all fields."""
        return MergeRequest(
            number=42,
            title="Fix critical bug",
            description="This PR fixes the login issue",
            author="developer",
            source_branch="fix/login",
            target_branch="main",
            comments=(
                Comment(author="reviewer", body="Needs tests"),
                Comment(author="developer", body="Added tests"),
            ),
            changes=(
                FileChange(
                    filename="src/auth.py",
                    change_type=FileChangeType.MODIFIED,
                    additions=20,
                    deletions=5,
                ),
                FileChange(
                    filename="tests/test_auth.py",
                    change_type=FileChangeType.ADDED,
                    additions=50,
                    deletions=0,
                ),
            ),
            url="https://github.com/owner/repo/pull/42",
            created_at=datetime(2026, 1, 15, tzinfo=UTC),
            updated_at=datetime(2026, 1, 20, tzinfo=UTC),
        )

    def test_create_minimal_mr(self, minimal_mr: MergeRequest) -> None:
        """Test creating MR with minimal fields."""
        assert minimal_mr.number == 1
        assert minimal_mr.title == "Add new feature"
        assert minimal_mr.description == ""
        assert minimal_mr.comments == ()
        assert minimal_mr.changes == ()

    def test_create_full_mr(self, full_mr: MergeRequest) -> None:
        """Test creating MR with all fields."""
        assert full_mr.number == 42
        assert len(full_mr.comments) == 2
        assert len(full_mr.changes) == 2

    def test_total_additions(self, full_mr: MergeRequest) -> None:
        """Test total_additions property."""
        assert full_mr.total_additions == 70  # 20 + 50

    def test_total_deletions(self, full_mr: MergeRequest) -> None:
        """Test total_deletions property."""
        assert full_mr.total_deletions == 5

    def test_files_changed(self, full_mr: MergeRequest) -> None:
        """Test files_changed property."""
        assert full_mr.files_changed == 2

    def test_mr_number_positive(self) -> None:
        """Test that MR number must be positive."""
        with pytest.raises(ValidationError):
            MergeRequest(
                number=0,
                title="Test",
                author="dev",
                source_branch="feature",
                target_branch="main",
            )

    def test_mr_title_required(self) -> None:
        """Test that title is required."""
        with pytest.raises(ValidationError):
            MergeRequest(
                number=1,
                author="dev",
                source_branch="feature",
                target_branch="main",
            )  # type: ignore[call-arg]

    def test_mr_title_not_empty(self) -> None:
        """Test that title cannot be empty."""
        with pytest.raises(ValidationError):
            MergeRequest(
                number=1,
                title="",
                author="dev",
                source_branch="feature",
                target_branch="main",
            )

    def test_mr_is_frozen(self, minimal_mr: MergeRequest) -> None:
        """Test that MR model is immutable."""
        with pytest.raises(ValidationError):
            minimal_mr.title = "Modified"  # type: ignore[misc]

    def test_mr_datetime_must_be_timezone_aware(self) -> None:
        """Test that created_at and updated_at reject naive datetime."""
        naive_dt = datetime(2026, 1, 20, 12, 0, 0)  # noqa: DTZ001 - intentionally naive

        with pytest.raises(ValidationError) as exc_info:
            MergeRequest(
                number=1,
                title="Test",
                author="dev",
                source_branch="feature",
                target_branch="main",
                created_at=naive_dt,
            )
        assert "timezone-aware" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            MergeRequest(
                number=1,
                title="Test",
                author="dev",
                source_branch="feature",
                target_branch="main",
                updated_at=naive_dt,
            )
        assert "timezone-aware" in str(exc_info.value)


class TestLinkedTask:
    """Tests for LinkedTask model."""

    def test_create_minimal_task(self) -> None:
        """Test creating a task with minimal fields."""
        task = LinkedTask(identifier="123", title="Implement feature X")
        assert task.identifier == "123"
        assert task.title == "Implement feature X"
        assert task.description == ""
        assert task.url is None

    def test_create_full_task(self) -> None:
        """Test creating a task with all fields."""
        task = LinkedTask(
            identifier="PROJ-456",
            title="Add authentication",
            description="Implement OAuth2 authentication flow",
            url="https://jira.example.com/PROJ-456",
        )
        assert task.identifier == "PROJ-456"
        assert task.url == "https://jira.example.com/PROJ-456"

    def test_task_identifier_required(self) -> None:
        """Test that identifier is required."""
        with pytest.raises(ValidationError):
            LinkedTask(title="Test")  # type: ignore[call-arg]

    def test_task_identifier_not_empty(self) -> None:
        """Test that identifier cannot be empty."""
        with pytest.raises(ValidationError):
            LinkedTask(identifier="", title="Test")


class TestReviewContext:
    """Tests for ReviewContext model."""

    @pytest.fixture
    def sample_mr(self) -> MergeRequest:
        """Create a sample MR for testing."""
        return MergeRequest(
            number=1,
            title="Test PR",
            author="dev",
            source_branch="feature",
            target_branch="main",
        )

    @pytest.fixture
    def sample_task(self) -> LinkedTask:
        """Create a sample task for testing."""
        return LinkedTask(identifier="123", title="Test task")

    def test_create_context_without_task(self, sample_mr: MergeRequest) -> None:
        """Test creating context without linked task."""
        context = ReviewContext(mr=sample_mr, repository="owner/repo")
        assert context.mr == sample_mr
        assert context.task is None
        assert context.repository == "owner/repo"
        assert context.has_linked_task is False

    def test_create_context_with_task(
        self, sample_mr: MergeRequest, sample_task: LinkedTask
    ) -> None:
        """Test creating context with linked task."""
        context = ReviewContext(mr=sample_mr, task=sample_task, repository="owner/repo")
        assert context.task == sample_task
        assert context.has_linked_task is True

    def test_repository_format_valid(self, sample_mr: MergeRequest) -> None:
        """Test that valid repository formats are accepted."""
        context = ReviewContext(mr=sample_mr, repository="owner/repo")
        assert context.repository == "owner/repo"

        context2 = ReviewContext(mr=sample_mr, repository="org-name/repo-name")
        assert context2.repository == "org-name/repo-name"

    def test_repository_format_invalid_no_slash(self, sample_mr: MergeRequest) -> None:
        """Test that repository without slash is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReviewContext(mr=sample_mr, repository="invalid")
        assert "owner/repo" in str(exc_info.value)

    def test_repository_format_invalid_empty_parts(self, sample_mr: MergeRequest) -> None:
        """Test that repository with empty parts is rejected."""
        with pytest.raises(ValidationError):
            ReviewContext(mr=sample_mr, repository="/repo")

        with pytest.raises(ValidationError):
            ReviewContext(mr=sample_mr, repository="owner/")

    def test_repository_format_invalid_multiple_slashes(self, sample_mr: MergeRequest) -> None:
        """Test that repository with multiple slashes is rejected."""
        with pytest.raises(ValidationError):
            ReviewContext(mr=sample_mr, repository="owner/repo/extra")


class TestVulnerability:
    """Tests for Vulnerability model."""

    def test_create_minimal_vulnerability(self) -> None:
        """Test creating a vulnerability with minimal fields."""
        vuln = Vulnerability(
            title="SQL Injection",
            description="User input not sanitized",
            severity=VulnerabilitySeverity.CRITICAL,
        )
        assert vuln.title == "SQL Injection"
        assert vuln.severity == VulnerabilitySeverity.CRITICAL
        assert vuln.file is None
        assert vuln.line is None
        assert vuln.recommendation == ""

    def test_create_full_vulnerability(self) -> None:
        """Test creating a vulnerability with all fields."""
        vuln = Vulnerability(
            title="XSS Vulnerability",
            description="Output not escaped in template",
            severity=VulnerabilitySeverity.HIGH,
            file="src/templates/user.html",
            line=42,
            recommendation="Use escape filter",
        )
        assert vuln.file == "src/templates/user.html"
        assert vuln.line == 42
        assert vuln.recommendation == "Use escape filter"

    def test_vulnerability_line_must_be_positive(self) -> None:
        """Test that line number must be positive."""
        with pytest.raises(ValidationError):
            Vulnerability(
                title="Test",
                description="Test",
                severity=VulnerabilitySeverity.LOW,
                line=0,
            )

    def test_all_severity_levels(self) -> None:
        """Test all vulnerability severity levels."""
        for severity in VulnerabilitySeverity:
            vuln = Vulnerability(
                title="Test",
                description="Test",
                severity=severity,
            )
            assert vuln.severity == severity


class TestReviewResult:
    """Tests for ReviewResult model."""

    @pytest.fixture
    def critical_vuln(self) -> Vulnerability:
        """Create a critical vulnerability."""
        return Vulnerability(
            title="Critical issue",
            description="Critical description",
            severity=VulnerabilitySeverity.CRITICAL,
        )

    @pytest.fixture
    def high_vuln(self) -> Vulnerability:
        """Create a high severity vulnerability."""
        return Vulnerability(
            title="High issue",
            description="High description",
            severity=VulnerabilitySeverity.HIGH,
        )

    @pytest.fixture
    def low_vuln(self) -> Vulnerability:
        """Create a low severity vulnerability."""
        return Vulnerability(
            title="Low issue",
            description="Low description",
            severity=VulnerabilitySeverity.LOW,
        )

    def test_create_empty_result(self) -> None:
        """Test creating an empty review result."""
        result = ReviewResult()
        assert result.vulnerabilities == ()
        assert result.task_alignment == TaskAlignmentStatus.INSUFFICIENT_DATA
        assert result.summary == ""
        assert result.has_critical_vulnerabilities is False
        assert result.vulnerability_count == 0
        assert result.matches_task is None

    def test_create_full_result(self, critical_vuln: Vulnerability) -> None:
        """Test creating a full review result."""
        now = datetime.now(tz=UTC)
        result = ReviewResult(
            vulnerabilities=(critical_vuln,),
            task_alignment=TaskAlignmentStatus.ALIGNED,
            task_alignment_reasoning="Changes match task requirements",
            summary="Found 1 critical vulnerability",
            reviewed_at=now,
        )
        assert len(result.vulnerabilities) == 1
        assert result.task_alignment == TaskAlignmentStatus.ALIGNED
        assert result.reviewed_at == now

    def test_has_critical_vulnerabilities(
        self, critical_vuln: Vulnerability, low_vuln: Vulnerability
    ) -> None:
        """Test has_critical_vulnerabilities property."""
        result_with_critical = ReviewResult(vulnerabilities=(critical_vuln,))
        assert result_with_critical.has_critical_vulnerabilities is True

        result_without_critical = ReviewResult(vulnerabilities=(low_vuln,))
        assert result_without_critical.has_critical_vulnerabilities is False

    def test_has_high_or_critical_vulnerabilities(
        self, critical_vuln: Vulnerability, high_vuln: Vulnerability, low_vuln: Vulnerability
    ) -> None:
        """Test has_high_or_critical_vulnerabilities property."""
        result_critical = ReviewResult(vulnerabilities=(critical_vuln,))
        assert result_critical.has_high_or_critical_vulnerabilities is True

        result_high = ReviewResult(vulnerabilities=(high_vuln,))
        assert result_high.has_high_or_critical_vulnerabilities is True

        result_low = ReviewResult(vulnerabilities=(low_vuln,))
        assert result_low.has_high_or_critical_vulnerabilities is False

    def test_vulnerability_count(
        self, critical_vuln: Vulnerability, low_vuln: Vulnerability
    ) -> None:
        """Test vulnerability_count property."""
        result = ReviewResult(vulnerabilities=(critical_vuln, low_vuln))
        assert result.vulnerability_count == 2

    def test_matches_task_aligned(self) -> None:
        """Test matches_task property when aligned."""
        result = ReviewResult(task_alignment=TaskAlignmentStatus.ALIGNED)
        assert result.matches_task is True

    def test_matches_task_misaligned(self) -> None:
        """Test matches_task property when misaligned."""
        result = ReviewResult(task_alignment=TaskAlignmentStatus.MISALIGNED)
        assert result.matches_task is False

    def test_matches_task_insufficient_data(self) -> None:
        """Test matches_task property when insufficient data."""
        result = ReviewResult(task_alignment=TaskAlignmentStatus.INSUFFICIENT_DATA)
        assert result.matches_task is None

    def test_result_is_frozen(self) -> None:
        """Test that result model is immutable."""
        result = ReviewResult()
        with pytest.raises(ValidationError):
            result.summary = "Modified"  # type: ignore[misc]

    def test_result_reviewed_at_must_be_timezone_aware(self) -> None:
        """Test that reviewed_at rejects naive datetime."""
        naive_dt = datetime(2026, 1, 20, 12, 0, 0)  # noqa: DTZ001 - intentionally naive
        with pytest.raises(ValidationError) as exc_info:
            ReviewResult(reviewed_at=naive_dt)
        assert "timezone-aware" in str(exc_info.value)


class TestEnums:
    """Tests for enum classes."""

    def test_comment_author_type_values(self) -> None:
        """Test CommentAuthorType enum values."""
        assert CommentAuthorType.USER.value == "user"
        assert CommentAuthorType.BOT.value == "bot"

    def test_file_change_type_values(self) -> None:
        """Test FileChangeType enum values."""
        assert FileChangeType.ADDED.value == "added"
        assert FileChangeType.MODIFIED.value == "modified"
        assert FileChangeType.DELETED.value == "deleted"
        assert FileChangeType.RENAMED.value == "renamed"

    def test_vulnerability_severity_values(self) -> None:
        """Test VulnerabilitySeverity enum values."""
        assert VulnerabilitySeverity.CRITICAL.value == "critical"
        assert VulnerabilitySeverity.HIGH.value == "high"
        assert VulnerabilitySeverity.MEDIUM.value == "medium"
        assert VulnerabilitySeverity.LOW.value == "low"
        assert VulnerabilitySeverity.INFO.value == "info"

    def test_task_alignment_status_values(self) -> None:
        """Test TaskAlignmentStatus enum values."""
        assert TaskAlignmentStatus.ALIGNED.value == "aligned"
        assert TaskAlignmentStatus.MISALIGNED.value == "misaligned"
        assert TaskAlignmentStatus.INSUFFICIENT_DATA.value == "insufficient_data"
