from random import randint

from .. import db

cities = [
    "basin-city",
    "bikini-bottom",
    "coruscant",
    "district-x",
    "gotham-city",
    "los-santos",
    "mos-eisley",
    "raccoon-city",
    "riverdale",
    "seaside-town",
    "springfield",
    "zion",
]


class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(
        db.String(40), nullable=False, unique=True, index=True
    )  # User#Discriminator
    city = db.Column(db.SmallInteger, default=randint(0, 11), nullable=False)
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
