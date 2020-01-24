import base64
import json
import os
import string
from random import randint

from Crypto import Random
from Crypto.PublicKey import RSA

# fmt: off
from flask import (abort, current_app, jsonify, redirect, render_template,
                   request, session, url_for)
from requests_oauthlib import OAuth2Session

from .. import db_session
from .forms import RecaptchaForm, SendMessageForm, ViewMessageForm
from .models import Message, MessageQueue, PasswordLink, Profile, cities

# fmt: on


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
    return jsonify(user)


def encrypt_message(a_message, publickey):
    encrypted_msg = publickey.encrypt(a_message, 32)[0]
    encoded_encrypted_msg = base64.b64encode(encrypted_msg)
    return encoded_encrypted_msg


def decrypt_message(encoded_encrypted_msg, privatekey):
    decoded_encrypted_msg = base64.b64decode(encoded_encrypted_msg)
    decoded_decrypted_msg = privatekey.decrypt(decoded_encrypted_msg)
    return decoded_decrypted_msg


ALPHABET = string.ascii_uppercase + string.digits + string.ascii_lowercase + "-_"
ALPHABET_REVERSE = dict((c, i) for (i, c) in enumerate(ALPHABET))
BASE = len(ALPHABET)
SIGN_CHARACTER = "$"


def num_encode(n):
    if n < 0:
        return SIGN_CHARACTER + num_encode(-n)
    s = []
    while True:
        n, r = divmod(n, BASE)
        s.append(ALPHABET[r])
        if n == 0:
            break
    return "".join(reversed(s))


def num_decode(s):
    if s[0] == SIGN_CHARACTER:
        return -num_decode(s[1:])
    n = 0
    for c in s:
        n = n * BASE + ALPHABET_REVERSE[c]
    return n


@current_app.route("/get-key-pair/{string: unique_id}", methods=["GET", "POST"])
def get_key_pair(unique_id):
    form = RecaptchaForm()
    if form.validate_on_submit():
        db_id = num_decode(unique_id)
        instance = db_session.query(PasswordLink.id).get(PasswordLink=db_id)
        if instance is None:
            return abort(404)
        db_session.delete(instance)
        db_session.commit()
        return render_template(
            "get_key_pair.html",
            public_key=instance.public,
            private_key=instance.private,
        )
    elif request.method == "GET":
        return render_template("key_pair_form.html", form=form)
    else:
        return abort(403)


@current_app.route("/send-message/discord-oauth/{string: unique_id}")
def send_message_oauth(unique_id):
    scope = request.args.get("scope", "identify")
    discord = make_session(scope=scope)
    authorization_url, state = discord.authorization_url(AUTHORIZATION_BASE_URL)
    session["oauth2_state"] = state
    return redirect(request.url_root + "send-message/" + unique_id)


@current_app.route("/add-message-to-queue", methods=["POST"])
def add_message_to_queue():
    """
    This is a filtration system so that users don't flood others'
    mailboxes with messages.
    I.e. there is a reCAPTCHA v2 system (does not track users).

    This route is in cooperation with the
    Kivy + Python Discord Code Jam 6 Amphibian Alchemists project.
    You can most certainly remove this route and MessageQueue and
    reconfigure the send_message route to avoid this functionality.
    """
    print(1)
    message = str(request.json.get("message"))
    if len(message) > 20000:
        return json.dumps({"response": "Too many characters. Delete some."})
    unique_id = randint(-9223372036854775808, 9223372036854775808)
    m = MessageQueue(message=message, id=unique_id)
    unique_id = num_encode(unique_id)
    db_session.add(m)
    db_session.commit()
    return json.dumps(
        {"response": "success", "data": f"{request.url_root}send-message/{unique_id}"}
    )


@current_app.route("/send-message/{string: unique_id}", methods=["GET", "POST"])
def send_message(unique_id):
    unique_id = num_decode(unique_id)

    if request.values.get("error"):
        return request.values["error"]
    discord = make_session(state=session.get("oauth2_state"))
    token = discord.fetch_token(
        TOKEN_URL,
        client_secret=OAUTH2_CLIENT_SECRET,
        authorization_response=request.url,
    )
    session["oauth2_token"] = token
    discord = make_session(token=session.get("oauth2_token"))
    user = discord.get(API_BASE_URL + "/users/@me").json()

    form = SendMessageForm()
    if form.validate_on_submit():
        instance = db_session.query(MessageQueue).get(MessageQueue=unique_id)
        sender_instance = db_session.query(Profile.id).get(Profile=user["id"])
        receiver_instance = db_session.query(Profile.id).get(
            Profile=request.values.get("receiver")
        )
        if instance is None or receiver_instance is None or sender_instance is None:
            return abort(404)
        message = Message(
            message=instance.message,
            sender_id=user["id"],
            receiver_id=receiver_instance.id,
        )
        db_session.add(message)
        db_session.delete(instance)
        db_session.commit()
        send_receiver_mail(mail_id=message.id, receiver_id=message.receiver_id)
        return jsonify(success="Check the server to make sure it sent!")
    elif request.method == "GET":
        return render_template("send_message.html", form=form)
    else:
        return abort(403)


@current_app.route("/view-message/{string: unique_id}", methods=["GET", "POST"])
def view_message(unique_id):
    form = ViewMessageForm()
    unique_id = num_decode(unique_id)
    instance = db_session.query(Message.id).get(Message=int(unique_id))
    if instance is None:
        return abort(404)
    if form.validate_on_submit():
        message = decrypt_message(instance.message, request.values.get("private_key"))
        return render_template("view_real_message.html", message=message)
    else:
        return render_template("view_message.html", message=instance.message)


def send_receiver_mail(mail_id, receiver_id):
    current_app.message_queue.put({'mail_id': mail_id, 'receiver_id': receiver_id})
