"""Views for the oauth app."""
import logging
import os

import jwt
from django.conf import settings
from django.core.files.base import ContentFile
from django.http import HttpResponse
from google_auth_oauthlib.flow import Flow

from oauth.utils import get_user_info

from .models import UserOAuth

logger = logging.getLogger(__name__)

JWT_SECRET = os.environ.get("JWT_SECRET_KEY")
API_CRED_PATH = os.path.join(settings.BASE_DIR, "secrets", "api_credentials.json")


def status(request):
    """Check if the user has authorized the app."""
    if 'Moodle-ID' not in request.headers.keys():
        return HttpResponse(status=400)

    moodle_id = request.headers['Moodle-ID']
    if not UserOAuth.objects.filter(user_id=moodle_id).exists():
        return HttpResponse(status=401)

    user = UserOAuth.objects.get(user_id=moodle_id)

    return HttpResponse(user.email, status=200)


def bind(request):
    """Binds user's google account to their Moodle ID."""

    # return 400 if Moodle-ID header is not present
    if 'Moodle-ID' not in request.headers.keys():
        return HttpResponse(status=400)

    moodle_id = request.headers['Moodle-ID']
    enc_jwt = jwt.encode({"MoodleID": moodle_id}, key=JWT_SECRET, algorithm='HS256')

    # create google oauth flow
    flow = Flow.from_client_secrets_file(
        API_CRED_PATH,
        scopes=[
            'openid',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/calendar',
        ],
        state=enc_jwt,
        redirect_uri=request.build_absolute_uri("/oauth/callback")
    )

    # redirect user to google oauth flow
    authorize_url, _ = flow.authorization_url(
        access_type='offline',
        prompt='consent',
        include_granted_scopes='true'
    )
    return HttpResponse(authorize_url)


def callback(request):
    """Callback for the google oauth flow."""

    state = request.GET.get('state')

    # return 400 if JWT is invalid
    try:
        enc_jwt = jwt.decode(state, JWT_SECRET, algorithms=['HS256'])
    except jwt.exceptions.InvalidSignatureError:
        return HttpResponse(status=400)
    user_id = enc_jwt['MoodleID']

    # retrieve user's oauth credentials
    flow = Flow.from_client_secrets_file(
        API_CRED_PATH,
        scopes=[
            'openid',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/calendar',
        ],
        state=request.GET.get('state'),
        redirect_uri=request.build_absolute_uri("/oauth/callback")
    )
    code = request.GET.get('code')
    flow.fetch_token(code=code)
    credentials = flow.credentials

    user_info = get_user_info(credentials)

    logger.info('Authorized user %s', user_info)

    # store oauth credentials in file and database
    file_content = ContentFile(credentials.to_json())
    if UserOAuth.objects.filter(user_id=int(user_id)).exists():
        obj = UserOAuth.objects.get(user_id=int(user_id))
        obj.oauth_credentials.delete()
    else:
        obj = UserOAuth(user_id=int(user_id))
    obj.email = user_info['email']
    obj.oauth_credentials.save(f'user_{user_id}.json', file_content)
    obj.save()
    return HttpResponse(credentials)
