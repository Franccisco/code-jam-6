# import os

from dotenv import load_dotenv








import os
from queue import Queue

from celery import Celery
import discord
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, orm

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(PROJECT_DIR, ".env")

# Flask setup
app = Flask(__name__, template_folder=os.path.join(PROJECT_DIR, os.path.normpath("dps/templates")))

app.debug = True
if app.debug:
    root_url = "http://localhost:5000"
else:
    root_url = "https://pythonanywhere.com"
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "setsecretkeyinnewdotenvfile")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
sqlite_path = "sqlite:///" + os.path.join(PROJECT_DIR, "app.db")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL") or sqlite_path

# Recaptcha
app.config["RECAPTCHA_USE_SSL"] = False
app.config["RECAPTCHA_PUBLIC_KEY"] = os.getenv("RECAPTCHA_PUBLIC_KEY")
app.config["RECAPTCHA_PRIVATE_KEY"] = os.getenv("RECAPTCHA_PRIVATE_KEY")
app.config["RECAPTCHA_OPTIONS"] = {"theme": "black"}

# Database
db = SQLAlchemy(app)
db.create_all()
migrate = Migrate(app, db)
engine = create_engine(sqlite_path, echo=app.debug)
db_session = orm.Session(engine)


# Celery setup
app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_RESULT_BACKEND='redis://localhost:6379'
)
celery = Celery(app.name, broker=app.config["CELERY_BROKER_URL"])
celery.conf.update(app.config)

# Setting up Discord Bot
discord_client = discord.Client()

from random import randint


cities = [
    (668562935005839381, "basin-city"),
    (668563954926092300, "bikini-bottom"),
    (668563327047172096, "coruscant"),
    (668563053645660175, "district-x"),
    (668563106880028680, "gotham-city"),
    (668563579393540096, "los-santos"),
    (668563282680086539, "mos-eisley"),
    (668563624431976448, "raccoon-city"),
    (668563164513697822, "riverdale"),
    (668563665636687892, "seaside-town"),
    (668564093921132545, "springfield"),
    (668563231740133396, "zion"),
]


class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    user = db.Column(
        db.String(40), nullable=False, unique=True, index=True
    )  # User#Discriminator
    city = db.Column(db.BigInteger, default=randint(0, 11), nullable=False)
    public_key = db.Column(db.String, nullable=False)
    # Relationships
    sent_message = db.relationship(
        "Message", backref="sender", lazy="dynamic", foreign_keys="Message.sender_id"
    )
    received_message = db.relationship(
        "Message",
        backref="receiver",
        lazy="dynamic",
        foreign_keys="Message.receiver_id",
    )


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    sender_id = db.Column(
        db.Integer, db.ForeignKey(Profile.id, ondelete="SET NULL"), nullable=True
    )
    receiver_id = db.Column(
        db.Integer, db.ForeignKey(Profile.id, ondelete="SET NULL"), nullable=True
    )
    message = db.Column(db.String(1000000), nullable=False)


class MessageQueue(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    message = db.Column(db.String(20000), nullable=False)


class PasswordLink(db.Model):
    # For Private-Public key pair sharing
    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    public = db.Column(db.String(10000))
    private = db.Column(db.String(10000))


import base64
import json
import os
import string
from random import randint

from Crypto import Random
from Crypto.PublicKey import RSA

# fmt: off
from flask import (abort, jsonify, redirect, render_template,
                   request, session, url_for)
from requests_oauthlib import OAuth2Session
# fmt: on

from random import randint
import string
import asyncio

from queue import Empty

from Crypto import Random
from Crypto.PublicKey import RSA

PERMISSIONS = [
    (669690836656848924, "basin-city"),
    (668564156697542667, "bikini-bottom"),
    (669690890616438787, "coruscant"),
    (669690948858675200, "district-x"),
    (669690975270207489, "gotham-city"),
    (669690994509348875, "los-santos"),
    (669691022367784961, "mos-eisley"),
    (669691047139606531, "raccoon-city"),
    (669691076197744680, "riverdale"),
    (669691090357714966, "seaside-town"),
    (669691110821724161, "springfield"),
    (669691140492099596, "zion"),
]


def num_encode(n):
    ALPHABET = string.ascii_uppercase + string.digits + string.ascii_lowercase + "-_"
    if n < 0:
        return "$" + num_encode(-n)
    s = []
    while True:
        n, r = divmod(n, len(ALPHABET))
        s.append(ALPHABET[r])
        if n == 0:
            break
    return "".join(reversed(s))


@discord_client.event
async def on_ready():
    print("We have logged in as {0.user}".format(discord_client))


def generate_keys():
    modulus_length = 2048
    private_key = RSA.generate(modulus_length, Random.new().read)
    public_key = private_key.publickey()
    return private_key, public_key


@discord_client.event
async def on_member_join(member):
    """
    Gets new member's username. Save it. Send user private and public key for
    future encryption via a one-time use link. This is so it's inaccessible
    afterwards. Will need to add recaptcha to this app.
    """
    # Logging user
    channel_id = cities[randint(0, len(cities))][0]
    username = member.name + member.discriminator
    private, public = generate_keys()
    new_user = Profile(id=member.id, user=username, city=channel_id, public_key=public)

    # Creating key pair
    unique_id = randint(-9223372036854775808, 9223372036854775808)
    unique_id = num_encode(unique_id)
    pw_link = PasswordLink(id=unique_id, public=public, private=private)

    # Adding to DB
    db_session.add_all([new_user, pw_link])
    db_session.commit()

    # Sending user the one-time-use key pair link
    await member.create_dm()
    await member.dm_channel.send(
        f"Hi {member.name}, welcome to my Discord Postal Service, safely "
        f"delivering your mail unless the mailer is mulled by a polar bear, "
        f"killed by a psychotic rat, or hopped on the wrong train!\nThis link "
        f"goes to your password for decrypting all future messages. We do not "
        f"save your password and think link only works once! So copy this down "
        f"somewhere, and DON'T LOSE IT!\n"
        f"{root_url}/get-password/{unique_id}"
    )


async def send_receiver_mail(mail_id, receiver_id):
    receiver_city = db_session.query(Profile.city).get(Profile=receiver_id)
    instance = db_session.query(Message.id).get(Message=mail_id)
    if instance is not None:
        channel = discord_client.get_channel(receiver_city)
        await channel.send(f"PONG <@{receiver_id}> {instance.message}")


async def handle_flask_data():
    while True:
        try:
            data = discord_client.message_queue.get(block=False)
            await send_receiver_mail(**data)
            discord_client.message_queue.task_done()
        except Empty:
            pass
        await asyncio.sleep(1)


discord_client.loop.create_task(handle_flask_data())

from flask_wtf import Form, RecaptchaField
from wtforms import PasswordField, StringField, validators


class RecaptchaForm(Form):
    """
    Used by password link and sending message.
    """

    recaptcha = RecaptchaField()


class SendMessageForm(Form):
    receiver = StringField("TO: ", [validators.DataRequired()])
    recaptcha = RecaptchaField()


class ViewMessageForm(Form):
    private_key = PasswordField("Your private key: ", [validators.DataRequired()])


OAUTH2_CLIENT_ID = os.getenv("OAUTH2_CLIENT_ID")
OAUTH2_CLIENT_SECRET = os.getenv("OAUTH2_CLIENT_SECRET")
if app.debug:
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


@app.errorhandler(MissingData)
def missing_data(error):
    return (
        json.dumps(
            {"response": "fail", "data": "request did not contain required data"}
        ),
        400,
    )


@app.errorhandler(MessageNotFound)
def missing_message(error):
    return (
        json.dumps({"response": "fail", "data": f"message not found with id: {error}"}),
        400,
    )


@app.errorhandler(404)
def four_zero_four(error):
    return json.dumps({"response": "fail", "data": "not found"}), 404


@app.route("/")  # TODO Add a delete user in case private key not saved
def index():
    scope = request.args.get("scope", "identify")
    discord = make_session(scope=scope)
    authorization_url, state = discord.authorization_url(AUTHORIZATION_BASE_URL)
    session["oauth2_state"] = state
    return redirect(authorization_url)


@app.route("/callback")
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


@app.route("/me")
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


@app.route("/get-key-pair/{string: unique_id}", methods=["GET", "POST"])
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


@app.route("/send-message/discord-oauth/{string: unique_id}")
def send_message_oauth(unique_id):
    scope = request.args.get("scope", "identify")
    discord = make_session(scope=scope)
    authorization_url, state = discord.authorization_url(AUTHORIZATION_BASE_URL)
    session["oauth2_state"] = state
    return redirect(request.url_root + "send-message/" + unique_id)


@app.route("/add-message-to-queue", methods=["POST"])
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


@app.route("/send-message/{string: unique_id}", methods=["GET", "POST"])
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


@app.route("/view-message/{string: unique_id}", methods=["GET", "POST"])
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
    app.message_queue.put({'mail_id': mail_id, 'receiver_id': receiver_id})

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(PROJECT_DIR, ".env")

DISCORD_PERMISSION_INT = 268658688


@celery.task
def start_discord():
    discord_client.run(os.getenv("DISCORD_BOT_TOKEN"))


if __name__ == "__main__":
    # Load Env Vars
    load_dotenv(dotenv_path=env_path)
    # Begin Discord bot
    start_discord.delay()
    # Start app
    app.run()
    db.create_all()
