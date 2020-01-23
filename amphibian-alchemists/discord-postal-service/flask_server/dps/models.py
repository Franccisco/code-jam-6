from random import randint

from .. import db

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
