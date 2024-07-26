"""Views for the calendar_sync app."""
from __future__ import annotations

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from oauth.models import UserOAuth

from . import sync


def trigger_sync(user_id: int, session_id: str):
    config = sync.config.load_config()
    config['moodle_session_id'] = session_id

    user_token_path = UserOAuth.objects.get(user_id=user_id).oauth_credentials.path
    config['google_token_path'] = user_token_path
    sync.main.sync(config)


@csrf_exempt
def calendar_sync(request):
    """Fetch user's Moodle calendar and sync with Google Calendar."""
    if request.method == 'POST':
        # return 400 if Moodle-Session header is not present
        if 'Moodle-Session' not in request.headers.keys():
            return HttpResponse(status=400)
        if 'Moodle-ID' not in request.headers.keys():
            return HttpResponse(status=400)

        session_id = request.headers['Moodle-Session']
        user_id = int(request.headers['Moodle-ID'])
        trigger_sync(user_id, session_id)

        return HttpResponse(status=200)
    else:
        return HttpResponse(status=405)
