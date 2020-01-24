from random import randint
import string

from Crypto import Random
from Crypto.PublicKey import RSA

from .. import db_session, root_url
from .. import discord_client as client
from .models import Message, PasswordLink, Profile, cities

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


@client.event
async def on_ready():
    print("We have logged in as {0.user}".format(client))


def generate_keys():
    modulus_length = 2048
    private_key = RSA.generate(modulus_length, Random.new().read)
    public_key = private_key.publickey()
    return private_key, public_key


@client.event
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
        channel = client.get_channel(receiver_city)
        await channel.send(f"PONG <@{receiver_id}> {instance.message}")
