"""Utility functions for calendar sync."""
from __future__ import annotations

import datetime
import re
from typing import Any

from dateutil.relativedelta import relativedelta

from calendar_sync.sync.exceptions import SubmissionStatusError


def get_next_k_month_timestamp(k: int) -> list[int]:
    """
    Get timestamps that is within the next k months (include this month)
    """
    timestamps = []
    now = datetime.datetime.now()
    for i in range(k):
        year = now.year
        month = now.month + i
        if month > 12:
            month -= 12
            year += 1

        timestamps.append(int(datetime.datetime(year, month, 5).timestamp()))
    return timestamps


def parse_date(date_str: str) -> str:
    """Parse the date string to ISO format."""
    return re.sub(r'(\d+)年\s*(\d{1,2})月\s*(\d{1,2})日.*\)\s*(\d{1,2}:\d{1,2}).*', r'\1-\2-\3T\4',
                  date_str) + ":00"


def get_cal_id(calendars: list[dict[str, Any]], summary: str) -> str | None:
    """Get the ID of the calendar with the given summary."""
    for cal in calendars:
        if cal['summary'] == summary:
            return cal['id']
    return None


def get_iso_format_date(
        date: datetime, delta_year: int = 0, delta_month: int = 0, delta_day: int = 0) -> str:
    """Get the ISO format date string with the given date and delta."""
    date = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    date += relativedelta(years=delta_year, months=delta_month, days=delta_day)
    return date.isoformat() + '+08:00'


def get_color_id(can_submit: bool, submission_status: str) -> int:
    """Get the color ID of the event based on the submission status."""
    if not can_submit or not submission_status or submission_status == 'unknown':
        return 8    # gray
    elif submission_status == 'not_submitted':
        return 11   # red
    elif submission_status == 'submitted':
        return 2    # green
    else:
        raise SubmissionStatusError(f'Unexpected submission status: {submission_status}')


def event_identical(event: dict[str, Any], assign: dict[str, Any]) -> bool:
    """Check if two events are identical."""
    if event['summary'] != assign['title']:
        return False
    if event['description'] != assign['description']:
        return False
    if event['start']['dateTime'] != assign['deadline']:
        return False
    if event['end']['dateTime'] != assign['deadline']:
        return False
    if event['colorId'] != str(get_color_id(assign['can_submit'], assign['submission_status'])):
        return False
    return True
