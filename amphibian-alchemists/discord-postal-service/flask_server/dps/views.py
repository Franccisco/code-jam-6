import base64
import json
import os
import string
from random import randint

from Crypto import Random
from Crypto.PublicKey import RSA
from flask import current_app, jsonify, redirect, request, session, url_for
from requests_oauthlib import OAuth2Session
from sqlalchemy import exc

from .models import Message, MessageQueue, Profile, db, cities

OAUTH2_CLIENT_ID = os.getenv("OAUTH2_CLIENT_ID")
OAUTH2_CLIENT_SECRET = os.getenv("OAUTH2_CLIENT_SECRET")
if current_app.debug:
    OAUTH2_REDIRECT_URI = "http://localhost:5000/callback"
else:
    OAUTH2_REDIRECT_URI = "https://blah.com"  # TODO In production, change to URL

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
        auto_refresh_kwargs={
            "client_id": OAUTH2_CLIENT_ID,
            "client_secret": OAUTH2_CLIENT_SECRET,
        },
        auto_refresh_url=TOKEN_URL,
        token_updater=token_updater,
    )


class MissingData(Exception):
    pass


class MessageNotFound(Exception):
    pass


@current_app.errorhandler(MissingData)
def missing_data(error):
    return (
        json.dumps(
            {"response": "fail", "data": "request did not contain required data"}
        ),
        400,
    )


@current_app.errorhandler(MessageNotFound)
def missing_message(error):
    return (
        json.dumps({"response": "fail", "data": f"message not found with id: {error}"}),
        400,
    )


@current_app.errorhandler(404)
def four_zero_four(error):
    return json.dumps({"response": "fail", "data": "not found"}), 404


@current_app.route("/")  # TODO Add a delete user in case private key not saved
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
        TOKEN_URL,
        client_secret=OAUTH2_CLIENT_SECRET,
        authorization_response=request.url,
    )
    session["oauth2_token"] = token
    return redirect(url_for(".me"))


def generate_keys():
    modulus_length = 2048
    private_key = RSA.generate(modulus_length, Random.new().read)
    public_key = private_key.publickey()
    return private_key, public_key


@current_app.route("/me")
def me():
    # TODO Add profile and settings, including deletion of acc and showing public key
    # TODO Also allow showing chat history.
    """
    It is to be reminded that if a user loses a public private key,
    then they're screwed. We ain't giving them their chat history
    that is, well, encrypted. Simply bye-bye.

    A lot of this is not correct.
    """
    discord = make_session(token=session.get("oauth2_token"))
    user = discord.get(API_BASE_URL + "/users/@me").json()
    full_username = user["username"] + "#" + user["discriminator"]
    try:
        # TODO Actually output useful info
        user = Profile.query.get(user=full_username)
        return jsonify(user)
    except exc.SQLAlchemyError:
        # TODO REMOVE! This is only for testing.
        """
        When we implement the bot, we will need to let it check
        audit logs to see which user joins.
        
        When an exception arises, simply pass during production environment
        """
        private, public = generate_keys()
        city = cities[randint(0, len(cities))]
        user = Profile(user=full_username, city=city, public_key=public)
        db.session.add(user)
        db.session.commit()
        # TODO Add bot so that permission to add tag to user is allowed
        return jsonify(user=user, private_key=private)


def encrypt_message(a_message, publickey):
    encrypted_msg = publickey.encrypt(a_message, 32)[0]
    encoded_encrypted_msg = base64.b64encode(encrypted_msg)
    return encoded_encrypted_msg


def decrypt_message(encoded_encrypted_msg, privatekey):
    decoded_encrypted_msg = base64.b64decode(encoded_encrypted_msg)
    decoded_decrypted_msg = privatekey.decrypt(decoded_encrypted_msg)
    return decoded_decrypted_msg


ALPHABET = string.ascii_uppercase + string.digits + string.ascii_lowercase + '-_'
ALPHABET_REVERSE = dict((c, i) for (i, c) in enumerate(ALPHABET))
BASE = len(ALPHABET)
SIGN_CHARACTER = '$'


def num_encode(n):
    if n < 0:
        return SIGN_CHARACTER + num_encode(-n)
    s = []
    while True:
        n, r = divmod(n, BASE)
        s.append(ALPHABET[r])
        if n == 0: break
    return ''.join(reversed(s))


def num_decode(s):
    if s[0] == SIGN_CHARACTER:
        return -num_decode(s[1:])
    n = 0
    for c in s:
        n = n * BASE + ALPHABET_REVERSE[c]
    return n


@current_app.route("/add-message-to-queue", methods=["POST"])
def add_message_to_queue():
    """
    This is a filtration system so that users don't flood others' mailboxes with messages.
    I.e. there is a reCAPTCHA v2 system (does not track users).

    This route is in cooperation with the Kivy + Python Discord Code Jam 6 Amphibian Alchemists project.
    You can most certainly remove this route and MessageQueue and reconfigure the send_message route
    to avoid this functionality.
    """
    message = str(request.json.get("message"))
    if len(message) > 20000:
        return json.dumps({"response": "Too many characters. Delete some."})
    unique_id = randint(-9223372036854775808, 9223372036854775808)
    m = MessageQueue(message=message, id=unique_id)
    unique_id = num_encode(unique_id)
    db.session.add(m)
    db.session.commit()
    return json.dumps(
        {"response": "success", "data": f"{request.url_root}send-message/{unique_id}"}
    )


@current_app.route("/send-message/<string: unique_id>", methods=["GET"])
def send_message(unique_id):
    # TODO read the docs above for what to do next here
    num_decode(unique_id)
    # This is when a message is generated from the form
    new_id = 1
    num_encode(new_id)


@current_app.route("/view-message/<string: unique_id>", methods=["GET"])
def view_message(unique_id):
    num_decode(unique_id)
    message = Message.queue.get()
    decrypt_message(message.message)
