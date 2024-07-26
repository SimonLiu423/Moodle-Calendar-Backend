"""
Interacting with multiple calendar APIs.
Currently supports Google Calendar API only.
"""
from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


class GoogleCalendar:
    """
    Interact with Google Calendar API.
    """

    def __init__(self, credentials_path: Path | str, user_token_path: Path | str) -> None:
        self.scopes = [
            'openid',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/calendar',
        ]
        self.timezone = 'Asia/Taipei'
        self.credentials = self.load_credentials(credentials_path, user_token_path)
        self.service = self.build_service()

    def load_credentials(
            self, credentials_path: Path | str, user_token_path: Path | str) -> Credentials:
        """
        Load credentials from file.
        """
        cred = None
        if os.path.exists(user_token_path):
            logger.debug('Loading credentials from "%s".', user_token_path)
            cred = Credentials.from_authorized_user_file(user_token_path, self.scopes)

        if not cred or not cred.valid:
            if cred and cred.expired and cred.refresh_token:
                # if the credentials are invalid, refresh them
                logger.debug('Invalid credentials, refreshing...')
                cred.refresh(Request())
            else:
                logger.debug('No valid credentials, requesting new credentials...')
                cred = self.request_authorization(credentials_path)

        return cred

    def request_authorization(self, credentials_path: Path | str) -> Credentials:
        """
        Request user's authorization.
        Launches a local server to handle the OAuth 2.0 dance.
        """
        flow = InstalledAppFlow.from_client_secrets_file(credentials_path, self.scopes)
        cred = flow.run_local_server(port=0)
        return cred

    def build_service(self):
        """Build service object."""
        return build('calendar', 'v3', credentials=self.credentials)

    def list_calendars(self):
        """Lists all calendars the user has."""
        logger.debug('Listing calendars...')
        calendars = self.service.calendarList().list().execute()
        return calendars.get('items', [])

    def create_calendar(self, summary: str, description: str) -> str:
        """
        Creates a new calendar with the given summary and description.
        Returns the ID of the new calendar.
        """
        calendar = {
            'summary': summary,
            'description': description,
            'timeZone': self.timezone,
        }
        calendar = self.service.calendars().insert(body=calendar).execute()
        return calendar.get('id')

    def create_event(
            self, calendar_id: str, title: str, start_time: str, end_time: str, description: str,
            color_id: str = "1") -> str:
        """
        Creates a new event in the given calendar id.
        Returns the HTML link of the new event.
        """
        event = {
            'summary': title,
            'description': description,
            'start': {
                'dateTime': start_time,
                'timeZone': self.timezone
            },
            'end': {
                'dateTime': end_time,
                'timeZone': self.timezone
            },
            'colorId': color_id,
        }
        event = self.service.events().insert(calendarId=calendar_id, body=event).execute()
        return event.get('htmlLink')

    def update_event(
            self, calendar_id: str, event_id: str, title: str, start_time: str, end_time: str,
            description: str, color_id: str = "1") -> str:
        """Updates an existing event in the given calendar id."""

        event = {
            'summary': title,
            'description': description,
            'start': {
                'dateTime': start_time,
                'timeZone': self.timezone,
            },
            'end': {
                'dateTime': end_time,
                'timeZone': self.timezone,
            },
            'colorId': color_id,
        }
        events = self.service.events()
        event = events.update(calendarId=calendar_id, eventId=event_id, body=event).execute()
        return event.get('htmlLink')

    def delete_event(self, calendar_id: str, event_id: str) -> None:
        """Deletes an event with the given id."""
        self.service.events().delete(calendarId=calendar_id, eventId=event_id).execute()

    def list_events(self, calendar_id: str, time_min: str, time_max: str) -> list[dict[str, Any]]:
        """Lists events of a calendar in the given time range."""
        events = self.service.events()
        filtered_events = events.list(calendarId=calendar_id,
                                      timeMin=time_min, timeMax=time_max).execute()
        return filtered_events.get('items', [])

    def get_colors(self) -> dict[str, Any]:
        """Gets all available colors."""
        colors = self.service.colors().get().execute()
        return colors
