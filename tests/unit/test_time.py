"""Unit tests for time utilities."""

from datetime import UTC, datetime, timedelta, timezone

from ai_reviewer.utils.time import ensure_timezone


class TestEnsureTimezone:
    """Tests for ensure_timezone function."""

    def test_naive_datetime_gets_utc(self) -> None:
        """Test that naive datetime gets UTC timezone."""
        naive = datetime(2024, 1, 15, 12, 30, 0)
        assert naive.tzinfo is None

        result = ensure_timezone(naive)

        assert result is not None
        assert result.tzinfo is not None
        assert result.tzinfo == UTC
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 12
        assert result.minute == 30
        assert result.second == 0

    def test_aware_datetime_unchanged(self) -> None:
        """Test that timezone-aware datetime is returned unchanged."""
        aware = datetime(2024, 1, 15, 12, 30, 0, tzinfo=UTC)

        result = ensure_timezone(aware)

        assert result is aware  # Same object
        assert result.tzinfo == UTC

    def test_aware_datetime_with_different_timezone_preserved(self) -> None:
        """Test that datetime with non-UTC timezone is preserved."""
        # Create a timezone with +2 hours offset
        tz_plus_2 = timezone(timedelta(hours=2))
        aware = datetime(2024, 1, 15, 12, 30, 0, tzinfo=tz_plus_2)

        result = ensure_timezone(aware)

        assert result is aware  # Same object, not modified
        assert result.tzinfo == tz_plus_2

    def test_none_returns_none(self) -> None:
        """Test that None input returns None."""
        result = ensure_timezone(None)
        assert result is None

    def test_naive_datetime_preserves_all_fields(self) -> None:
        """Test that all datetime fields are preserved when adding timezone."""
        naive = datetime(2024, 6, 15, 23, 59, 59, 123456)

        result = ensure_timezone(naive)

        assert result is not None
        assert result.year == 2024
        assert result.month == 6
        assert result.day == 15
        assert result.hour == 23
        assert result.minute == 59
        assert result.second == 59
        assert result.microsecond == 123456
        assert result.tzinfo == UTC

    def test_edge_case_midnight(self) -> None:
        """Test midnight datetime."""
        naive = datetime(2024, 1, 1, 0, 0, 0)

        result = ensure_timezone(naive)

        assert result is not None
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0
        assert result.tzinfo == UTC

    def test_edge_case_end_of_year(self) -> None:
        """Test end of year datetime."""
        naive = datetime(2024, 12, 31, 23, 59, 59)

        result = ensure_timezone(naive)

        assert result is not None
        assert result.month == 12
        assert result.day == 31
        assert result.hour == 23
        assert result.minute == 59
        assert result.second == 59
        assert result.tzinfo == UTC


class TestEnsureTimezoneTypeHints:
    """Tests for type hint overloads of ensure_timezone."""

    def test_return_type_with_datetime(self) -> None:
        """Test that return type is datetime when input is datetime."""
        dt = datetime(2024, 1, 15, 12, 30, 0)
        result = ensure_timezone(dt)
        # Type checker should know this is datetime, not None
        assert isinstance(result, datetime)

    def test_return_type_with_none(self) -> None:
        """Test that return type is None when input is None."""
        result = ensure_timezone(None)
        # Type checker should know this is None
        assert result is None
