"""
Main module for calendar sync.
"""
from __future__ import annotations

import datetime
import logging
from typing import Any

from calendar_sync.sync.calendar import GoogleCalendar
from calendar_sync.sync.crawler import MoodleCrawler
from calendar_sync.sync.utils import (event_identical, get_cal_id,
                                      get_color_id, get_iso_format_date)

logger = logging.getLogger(__name__)


def sync(config: dict[str, Any]) -> None:
    """
    Crawls the calendar of NCKU Moodle site and syncs it with Google Calendar.
    """
    calendar_client = GoogleCalendar(config['google_api_path'], config['google_token_path'])
    if config['login_with_token']:
        moodle_crawler = MoodleCrawler(session_id=config['moodle_session_id'])
    else:
        moodle_crawler = MoodleCrawler(login_cred_path=config['moodle_cred_path'])

    # get calendar id
    calendars = calendar_client.list_calendars()
    cal_id = get_cal_id(calendars, 'Moodle Deadline')
    if cal_id is None:
        logger.info('Moodle Deadline calendar not found, creating a new one.')
        cal_id = calendar_client.create_calendar('Moodle Deadline', 'Deadline from Moodle')
    else:
        logger.info('Moodle Deadline calendar exists, won\'t create a new one.')

    # get next k months assignment info
    k = config['num_of_months']
    assign_info = moodle_crawler.get_next_k_month_assign_info(k)
    logger.info('Found %d assignments for next %d months.', len(assign_info), k)

    # Update the calendar
    cal_events = calendar_client.list_events(cal_id, time_min=get_iso_format_date(
        datetime.datetime.now()),
        time_max=get_iso_format_date(
        datetime.datetime.now(),
        delta_month=k))

    for assign in assign_info:
        logger.debug('Processing assignment %s.', assign)

        color_id = get_color_id(assign['can_submit'], assign['submission_status'])

        # check if the assignment is already in the calendar
        exist = False
        for event in cal_events:
            # if the assignment is already in the calendar
            if event['summary'] == assign['title']:
                exist = True
                logger.debug('assignment already exists in calendar.')
                # update the event if the event is not identical
                if not event_identical(event, assign):
                    logger.debug('events are not identical, updating event.')
                    calendar_client.update_event(
                        cal_id, event['id'],
                        assign['title'],
                        assign['deadline'],
                        assign['deadline'],
                        assign['description'],
                        color_id=color_id)
                break

        # create the event if the assignment is not in the calendar
        if not exist:
            logger.debug('assignment does not exist in calendar, creating event.')
            calendar_client.create_event(
                cal_id, assign['title'],
                assign['deadline'],
                assign['deadline'],
                assign['description'],
                color_id=color_id)

    logger.info('All assignments for the next %d months have been synced.', k)
