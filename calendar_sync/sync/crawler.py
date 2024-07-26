"""Crawl data from NCKU Moodle site."""
from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

import bs4
import requests

from calendar_sync.sync.utils import get_next_k_month_timestamp, parse_date

from .exceptions import ElementNotFoundException

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)

MOODLE_URL = 'https://moodle.ncku.edu.tw'
LOGIN_URL = 'https://moodle.ncku.edu.tw/login/index.php'
CALENDAR_URL = 'https://moodle.ncku.edu.tw/calendar/view.php?view=month&time={}'

PARSER = 'html.parser'
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/53.0.2785.143 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


class MoodleCrawler:
    """Crawler that crawls the calendar of NCKU Moodle site."""

    def __init__(self, session_id: str | None = None, login_cred_path: Path | str | None = None):
        logger.debug('Initializing MoodleCrawler.')
        if session_id is None and login_cred_path is None:
            raise ValueError('Either session_id or login_cred_path must be specified.')

        self.login_token = None
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        if session_id:
            logger.debug('Setting Moodle session id to %s.', session_id)
            self.session.cookies.set('MoodleSession', session_id)
        elif login_cred_path:
            self.login(login_cred_path)

    def get_user_id(self) -> str:
        """Get the user id of the current user."""
        soup = bs4.BeautifulSoup(self.session.get(MOODLE_URL).text, PARSER)
        popover = soup.find('div', {'class': 'popover-region-notifications'})
        return popover['data-userid']

    def get_login_token(self):
        """Get the login token of the current user."""
        soup = bs4.BeautifulSoup(self.session.get(MOODLE_URL).text, PARSER)
        token = soup.find('input', {'name': 'logintoken'})['value']
        return token

    def login(self, cred_path: Path | str) -> None:
        """Login to Moodle with the given credentials in `cred_path`."""
        with open(cred_path, 'r', encoding='utf-8') as f:
            credentials = json.load(f)
            username = credentials['username']
            password = credentials['password']

        self.login_token = self.get_login_token()
        payload = {
            'Mime Type': 'application/x-www-form-urlencoded',
            'anchor': '',
            'username': username,
            'password': password,
            'logintoken': self.login_token,
        }
        self.session.post(LOGIN_URL, data=payload)

    def get_month_assign_urls(self, timestamps: list[int]) -> list[str]:
        """
        Fetch the URLs of the assignments in the given timestamps.
        `timestamps` is a list of Unix timestamps in the timezone of Asia/Taipei(UTC+8).
        This method will fetch and return all assignments in the month where the timestamps are.
        E.g. if the timestamps are [1722441600, 1725120000], which are the timestamps of 2024-08-01
        and 2024-09-01, this method will return the URLs of all assignments in the month of 2024-08
        and 2024-09.
        """
        assign_urls = []

        for timestamp in timestamps:
            soup = bs4.BeautifulSoup(self.session.get(
                CALENDAR_URL.format(timestamp)).text, PARSER)
            for event in soup.find_all('a', {'data-action': 'view-event'}):
                href = event['href']
                if 'assign' in href:
                    assign_urls.append(href)

        logger.info('Found %d assignments urls.', len(assign_urls))

        return assign_urls

    def get_assign_info(self, assign_url: str) -> dict[str, Any]:
        """Fetch the information of the assignment with the given URL."""
        soup = bs4.BeautifulSoup(self.session.get(assign_url).text, PARSER)
        assign_info = {
            'title': soup.find('div', {'role': 'main'}).find('h2').text.strip(),
            'can_submit': False,
            'deadline': None,
            'submission_status': None,
            'description': str(soup.find('div', {'id': 'intro'})),
        }

        # get submission allowed date
        submission_allowed_date_th = soup.find(
            'div', {'class': 'box py-3 generalbox boxaligncenter submissionsalloweddates'})
        if submission_allowed_date_th:
            assign_info['can_submit'] = False
        else:
            assign_info['can_submit'] = True

        # get submission status
        submission_status_th = soup.find('th', string='繳交狀態')
        if submission_status_th:
            submission_status_td = submission_status_th.find_next_sibling('td')
            submission_status = submission_status_td.text.strip() if submission_status_td else None
        else:
            raise ElementNotFoundException('Submission status element not found.')

        if submission_status in ['沒有繳交作業', '這個作業還沒人繳交']:
            assign_info['submission_status'] = 'not_submitted'
        elif submission_status.startswith('已繳交'):
            assign_info['submission_status'] = 'submitted'
        else:
            assign_info['submission_status'] = 'unknown'

        # Find the `<th>` tag by text and then the following `<td>` for the due date
        due_date_th = soup.find('th', string='規定繳交時間')
        if due_date_th:
            due_date_td = due_date_th.find_next_sibling('td')
            due_date = due_date_td.text.strip() if due_date_td else None
        else:
            raise ElementNotFoundException('Due date element not found.')

        # parse date
        assign_info['deadline'] = parse_date(due_date)

        return assign_info

    def get_next_k_month_assign_info(self, k: int) -> list[dict[str, Any]]:
        """Get the information of the next `k` months' assignments."""
        timestamps = get_next_k_month_timestamp(k=k)
        urls = self.get_month_assign_urls(timestamps)
        assign_info = []
        for url in urls:
            assign_info.append(self.get_assign_info(url))
        return assign_info
