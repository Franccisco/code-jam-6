import os

from flask import current_app, jsonify, redirect, request, session, url_for
from requests_oauthlib import OAuth2Session

from .models import Message, PasswordLink, Profile

OAUTH2_CLIENT_ID = os.getenv("OAUTH2_CLIENT_ID")
OAUTH2_CLIENT_SECRET = os.getenv("OAUTH2_CLIENT_SECRET")
if current_app.debug:
    OAUTH2_REDIRECT_URI = "http://localhost:5000/callback"
else:
    OAUTH2_REDIRECT_URI = "https://blah.com"

API_BASE_URL = os.environ.get("API_BASE_URL", "https://discordapp.com/api")
AUTHORIZATION_BASE_URL = API_BASE_URL + "/oauth2/authorize"
TOKEN_URL = API_BASE_URL + "/oauth2/token"

if "http://" in OAUTH2_REDIRECT_URI:
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "true"


def token_updater(token):
    session["oauth2_token"] = token


def make_session(token=None, state=None, scope=None):
    return OAuth2Session(
        client_id=OAUTH2_CLIENT_ID,
        token=token,
        state=state,
        scope=scope,
        redirect_uri=OAUTH2_REDIRECT_URI,
        auto_refresh_kwargs={"client_id": OAUTH2_CLIENT_ID, "client_secret": OAUTH2_CLIENT_SECRET,},
        auto_refresh_url=TOKEN_URL,
        token_updater=token_updater,
    )


@current_app.route("/")
def index():
    scope = request.args.get("scope", "identify")
    discord = make_session(scope=scope)
    authorization_url, state = discord.authorization_url(AUTHORIZATION_BASE_URL)
    session["oauth2_state"] = state
    return redirect(authorization_url)


@current_app.route("/callback")
def callback():
    if request.values.get("error"):
        return request.values["error"]
    discord = make_session(state=session.get("oauth2_state"))
    token = discord.fetch_token(
        TOKEN_URL, client_secret=OAUTH2_CLIENT_SECRET, authorization_response=request.url,
    )
    session["oauth2_token"] = token
    return redirect(url_for(".me"))


@current_app.route("/me")
def me():
    discord = make_session(token=session.get("oauth2_token"))
    user = discord.get(API_BASE_URL + "/users/@me").json()
    return jsonify(user=user)


# TODO Add a delete user in case private key not saved