"""Time utilities for AI Code Reviewer.

This module provides utilities for handling datetime objects,
particularly ensuring timezone awareness for Pydantic models.
"""

from __future__ import annotations

import datetime
from typing import overload


@overload
def ensure_timezone(dt: None) -> None: ...


@overload
def ensure_timezone(dt: datetime.datetime) -> datetime.datetime: ...


def ensure_timezone(dt: datetime.datetime | None) -> datetime.datetime | None:
    """Ensure a datetime object is timezone-aware.

    If the datetime is naive (no timezone info), it assumes UTC.
    If the datetime already has timezone info, it's returned unchanged.
    If None is passed, None is returned.

    This function is useful for normalizing datetime objects before
    storing them in Pydantic models that require timezone-aware datetimes.

    Args:
        dt: A datetime object or None.

    Returns:
        Timezone-aware datetime (with UTC if was naive) or None.

    Examples:
        >>> from datetime import datetime, UTC
        >>> naive = datetime(2024, 1, 15, 12, 30, 0)
        >>> aware = ensure_timezone(naive)
        >>> aware.tzinfo is not None
        True
        >>> aware.tzinfo == UTC
        True

        >>> already_aware = datetime(2024, 1, 15, 12, 30, 0, tzinfo=UTC)
        >>> result = ensure_timezone(already_aware)
        >>> result is already_aware
        True

        >>> ensure_timezone(None) is None
        True
    """
    if dt is None:
        return None

    if dt.tzinfo is None:
        # Naive datetime - assume UTC
        return dt.replace(tzinfo=datetime.UTC)

    # Already timezone-aware
    return dt


__all__ = ["ensure_timezone"]
