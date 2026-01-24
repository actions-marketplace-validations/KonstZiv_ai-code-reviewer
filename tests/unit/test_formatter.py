"""Unit tests for review formatter."""

from ai_reviewer.core.formatter import (
    RUSSIAN_DISCLAIMER,
    format_inline_comment,
    format_review_comment,
    is_russian_language,
)
from ai_reviewer.core.models import (
    CodeIssue,
    GoodPractice,
    IssueCategory,
    IssueSeverity,
    ReviewMetrics,
    ReviewResult,
    TaskAlignmentStatus,
)


class TestFormatReviewComment:
    """Tests for format_review_comment function."""

    def test_format_clean_result(self) -> None:
        """Test formatting a result with no issues."""
        result = ReviewResult(
            summary="Code looks good.",
            task_alignment=TaskAlignmentStatus.ALIGNED,
            task_alignment_reasoning="Matches requirements.",
        )

        comment = format_review_comment(result)

        assert "# 🤖 AI Code Review" in comment
        assert "## 📊 Summary" in comment
        assert "Code looks good." in comment
        assert "## 📋 Task Alignment" in comment
        assert "✅ Aligned" in comment
        assert "Matches requirements." in comment

    def test_format_with_issues(self) -> None:
        """Test formatting a result with issues."""
        issue = CodeIssue(
            category=IssueCategory.SECURITY,
            severity=IssueSeverity.CRITICAL,
            title="SQL Injection",
            description="Unsafe query execution",
            file_path="db.py",
            line_number=10,
            proposed_code='cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))',
        )
        result = ReviewResult(
            summary="Found issues.",
            issues=(issue,),
            task_alignment=TaskAlignmentStatus.INSUFFICIENT_DATA,
        )

        comment = format_review_comment(result)

        assert "## 🔒 Security" in comment
        assert "### 🔴 SQL Injection" in comment
        assert "`db.py:10`" in comment
        assert "Unsafe query execution" in comment
        assert "```suggestion" in comment
        assert "⚠️ Insufficient Data" in comment

    def test_format_with_good_practices(self) -> None:
        """Test formatting a result with good practices."""
        practice = GoodPractice(
            description="Excellent use of type hints",
            file_path="models.py",
        )
        result = ReviewResult(
            summary="Good code.",
            good_practices=(practice,),
            task_alignment=TaskAlignmentStatus.ALIGNED,
        )

        comment = format_review_comment(result)

        assert "## ✨ Good Practices" in comment
        assert "✨ Excellent use of type hints" in comment
        assert "`models.py`" in comment

    def test_format_summary_card(self) -> None:
        """Test that summary card shows correct counts."""
        issues = (
            CodeIssue(
                category=IssueCategory.SECURITY,
                severity=IssueSeverity.CRITICAL,
                title="Critical",
                description="Desc",
            ),
            CodeIssue(
                category=IssueCategory.CODE_QUALITY,
                severity=IssueSeverity.WARNING,
                title="Warning",
                description="Desc",
            ),
            CodeIssue(
                category=IssueCategory.PERFORMANCE,
                severity=IssueSeverity.INFO,
                title="Info",
                description="Desc",
            ),
        )
        practices = (GoodPractice(description="Good"),)
        result = ReviewResult(issues=issues, good_practices=practices)

        comment = format_review_comment(result)

        assert "| 🔴 Critical | 🟡 Warnings | 💡 Suggestions | ✨ Good Practices |" in comment
        assert "| 1 | 1 | 1 | 1 |" in comment

    def test_format_misaligned_task(self) -> None:
        """Test formatting a misaligned task result."""
        result = ReviewResult(
            summary="Logic error.",
            task_alignment=TaskAlignmentStatus.MISALIGNED,
            task_alignment_reasoning="Does not implement feature X.",
        )

        comment = format_review_comment(result)

        assert "❌ Misaligned" in comment
        assert "Does not implement feature X." in comment

    def test_format_with_learning_section(self) -> None:
        """Test formatting issue with why_matters and learn_more_url."""
        issue = CodeIssue(
            category=IssueCategory.SECURITY,
            severity=IssueSeverity.CRITICAL,
            title="XSS Vulnerability",
            description="User input not escaped",
            why_matters="XSS allows attackers to execute malicious scripts",
            learn_more_url="https://owasp.org/www-community/attacks/xss/",
        )
        result = ReviewResult(issues=(issue,))

        comment = format_review_comment(result)

        assert "<details>" in comment
        assert "<summary>💡 Why is this important?</summary>" in comment
        assert "XSS allows attackers" in comment
        assert "[Learn more](https://owasp.org" in comment
        assert "</details>" in comment

    def test_format_with_before_after(self) -> None:
        """Test formatting issue with existing and proposed code."""
        issue = CodeIssue(
            category=IssueCategory.CODE_QUALITY,
            severity=IssueSeverity.WARNING,
            title="Magic number",
            description="Use a named constant",
            existing_code="timeout = 30",
            proposed_code="timeout = DEFAULT_TIMEOUT",
        )
        result = ReviewResult(issues=(issue,))

        comment = format_review_comment(result)

        assert "**Before:**" in comment
        assert "timeout = 30" in comment
        assert "**After:**" in comment
        assert "```suggestion" in comment
        assert "timeout = DEFAULT_TIMEOUT" in comment

    def test_russian_language_includes_disclaimer(self) -> None:
        """Test that Russian language reviews include the disclaimer."""
        result = ReviewResult(
            summary="Код выглядит хорошо.",
            task_alignment=TaskAlignmentStatus.ALIGNED,
        )

        comment = format_review_comment(result, language="ru")

        assert RUSSIAN_DISCLAIMER in comment
        assert "Слава Украине!" in comment

    def test_russian_language_rus_code_includes_disclaimer(self) -> None:
        """Test that 'rus' (ISO 639-3) language code also includes disclaimer."""
        result = ReviewResult(
            summary="Код выглядит хорошо.",
            task_alignment=TaskAlignmentStatus.ALIGNED,
        )

        comment = format_review_comment(result, language="rus")

        assert RUSSIAN_DISCLAIMER in comment

    def test_non_russian_language_no_disclaimer(self) -> None:
        """Test that non-Russian languages don't include the disclaimer."""
        result = ReviewResult(
            summary="Code looks good.",
            task_alignment=TaskAlignmentStatus.ALIGNED,
        )

        for lang in ["en", "uk", "de", "fr", "es", None]:
            comment = format_review_comment(result, language=lang)
            assert RUSSIAN_DISCLAIMER not in comment

    def test_disclaimer_appears_before_footer(self) -> None:
        """Test that disclaimer appears before the footer."""
        result = ReviewResult(
            summary="Test.",
            task_alignment=TaskAlignmentStatus.ALIGNED,
        )

        comment = format_review_comment(result, language="ru")

        disclaimer_pos = comment.find("Слава Украине!")
        footer_pos = comment.find("Generated by")
        assert disclaimer_pos < footer_pos

    def test_categories_sorted_by_severity(self) -> None:
        """Test that categories with critical issues appear first."""
        issues = (
            CodeIssue(
                category=IssueCategory.PERFORMANCE,
                severity=IssueSeverity.INFO,
                title="Performance tip",
                description="Desc",
            ),
            CodeIssue(
                category=IssueCategory.SECURITY,
                severity=IssueSeverity.CRITICAL,
                title="Security issue",
                description="Desc",
            ),
        )
        result = ReviewResult(issues=issues)

        comment = format_review_comment(result)

        # Security should appear before Performance
        security_pos = comment.find("## 🔒 Security")
        performance_pos = comment.find("## ⚡ Performance")
        assert security_pos < performance_pos


class TestFormatInlineComment:
    """Tests for format_inline_comment function."""

    def test_format_minimal_inline(self) -> None:
        """Test formatting minimal inline comment."""
        issue = CodeIssue(
            category=IssueCategory.CODE_QUALITY,
            severity=IssueSeverity.WARNING,
            title="Unused import",
            description="This import is not used",
        )

        comment = format_inline_comment(issue)

        assert "🟡 **Unused import**" in comment
        assert "This import is not used" in comment
        assert "```suggestion" not in comment  # No suggestion

    def test_format_inline_with_suggestion(self) -> None:
        """Test formatting inline comment with suggestion."""
        issue = CodeIssue(
            category=IssueCategory.SECURITY,
            severity=IssueSeverity.CRITICAL,
            title="SQL Injection",
            description="Use parameterized query",
            proposed_code='cursor.execute("SELECT * FROM users WHERE id = ?", (id,))',
        )

        comment = format_inline_comment(issue)

        assert "🔴 **SQL Injection**" in comment
        assert "Use parameterized query" in comment
        assert "```suggestion" in comment
        assert 'cursor.execute("SELECT * FROM users WHERE id = ?", (id,))' in comment

    def test_format_inline_with_learn_more(self) -> None:
        """Test formatting inline comment with learn_more_url."""
        issue = CodeIssue(
            category=IssueCategory.SECURITY,
            severity=IssueSeverity.WARNING,
            title="Hardcoded secret",
            description="Don't hardcode secrets",
            learn_more_url="https://docs.example.com/secrets",
        )

        comment = format_inline_comment(issue)

        assert "📚 [Learn more](https://docs.example.com/secrets)" in comment

    def test_format_inline_is_compact(self) -> None:
        """Test that inline comment doesn't include verbose elements."""
        issue = CodeIssue(
            category=IssueCategory.SECURITY,
            severity=IssueSeverity.CRITICAL,
            title="Test",
            description="Desc",
            why_matters="Long explanation that should not appear in inline",
            existing_code="old code",
            proposed_code="new code",
        )

        comment = format_inline_comment(issue)

        # Should NOT include Before/After sections
        assert "**Before:**" not in comment
        # Should NOT include collapsible why_matters
        assert "<details>" not in comment
        assert "Why is this important?" not in comment
        # But SHOULD include the suggestion
        assert "```suggestion" in comment

    def test_format_inline_russian_disclaimer(self) -> None:
        """Test that inline comment includes Russian disclaimer when needed."""
        issue = CodeIssue(
            category=IssueCategory.CODE_QUALITY,
            severity=IssueSeverity.INFO,
            title="Test",
            description="Desc",
        )

        comment = format_inline_comment(issue, language="ru")

        assert RUSSIAN_DISCLAIMER in comment

    def test_format_inline_severity_icons(self) -> None:
        """Test that correct severity icons are used."""
        for severity, icon in [
            (IssueSeverity.CRITICAL, "🔴"),
            (IssueSeverity.WARNING, "🟡"),
            (IssueSeverity.INFO, "💡"),
        ]:
            issue = CodeIssue(
                category=IssueCategory.CODE_QUALITY,
                severity=severity,
                title="Test",
                description="Desc",
            )
            comment = format_inline_comment(issue)
            assert icon in comment


class TestIsRussianLanguage:
    """Tests for is_russian_language function."""

    def test_ru_is_russian(self) -> None:
        """Test that 'ru' is detected as Russian."""
        assert is_russian_language("ru") is True

    def test_rus_is_russian(self) -> None:
        """Test that 'rus' (ISO 639-3) is detected as Russian."""
        assert is_russian_language("rus") is True

    def test_case_insensitive(self) -> None:
        """Test that detection is case-insensitive."""
        assert is_russian_language("RU") is True
        assert is_russian_language("Ru") is True
        assert is_russian_language("RUS") is True

    def test_non_russian_languages(self) -> None:
        """Test that other languages are not detected as Russian."""
        assert is_russian_language("en") is False
        assert is_russian_language("uk") is False
        assert is_russian_language("de") is False
        assert is_russian_language("fr") is False

    def test_none_is_not_russian(self) -> None:
        """Test that None is not detected as Russian."""
        assert is_russian_language(None) is False

    def test_empty_string_is_not_russian(self) -> None:
        """Test that empty string is not detected as Russian."""
        assert is_russian_language("") is False


class TestFormatReviewCommentWithMetrics:
    """Tests for format_review_comment with metrics."""

    def test_format_with_metrics(self) -> None:
        """Test that metrics are displayed in footer."""
        metrics = ReviewMetrics(
            model_name="gemini-2.5-flash",
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500,
            api_latency_ms=1200,
            estimated_cost_usd=0.0002,
        )
        result = ReviewResult(
            summary="LGTM",
            task_alignment=TaskAlignmentStatus.ALIGNED,
            metrics=metrics,
        )

        comment = format_review_comment(result)

        assert "Model: gemini-2.5-flash" in comment
        assert "Tokens: 1,500" in comment
        assert "Latency: 1.2s" in comment
        assert "Est. cost: $0.0002" in comment

    def test_format_without_metrics(self) -> None:
        """Test that footer works without metrics."""
        result = ReviewResult(
            summary="LGTM",
            task_alignment=TaskAlignmentStatus.ALIGNED,
            metrics=None,
        )

        comment = format_review_comment(result)

        # Should still have footer
        assert "Generated by" in comment
        # But no metrics info
        assert "Model:" not in comment
        assert "Tokens:" not in comment

    def test_format_metrics_with_millisecond_latency(self) -> None:
        """Test that sub-second latency is displayed correctly."""
        metrics = ReviewMetrics(
            model_name="gemini-2.5-flash",
            api_latency_ms=750,
            estimated_cost_usd=0.0001,
        )
        result = ReviewResult(
            summary="Test",
            metrics=metrics,
        )

        comment = format_review_comment(result)

        assert "Latency: 750ms" in comment

    def test_format_metrics_with_large_cost(self) -> None:
        """Test that larger costs are displayed correctly."""
        metrics = ReviewMetrics(
            model_name="gemini-1.5-pro",
            prompt_tokens=100000,
            completion_tokens=50000,
            total_tokens=150000,
            api_latency_ms=5000,
            estimated_cost_usd=0.37,
        )
        result = ReviewResult(
            summary="Test",
            metrics=metrics,
        )

        comment = format_review_comment(result)

        assert "Est. cost: $0.37" in comment
        assert "Tokens: 150,000" in comment

    def test_metrics_appear_after_footer_separator(self) -> None:
        """Test that metrics appear in the footer section."""
        metrics = ReviewMetrics(
            model_name="gemini-2.5-flash",
            total_tokens=1000,
            api_latency_ms=500,
            estimated_cost_usd=0.0001,
        )
        result = ReviewResult(
            summary="Test",
            metrics=metrics,
        )

        comment = format_review_comment(result)

        # Footer separator should come before metrics
        separator_pos = comment.rfind("---")
        metrics_pos = comment.find("Model:")
        assert separator_pos < metrics_pos
