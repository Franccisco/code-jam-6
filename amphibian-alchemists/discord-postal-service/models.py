from random import randint

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

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
    user = db.Column(db.String(40), nullable=False, unique=True)  # User#Discriminator
    city = db.Column(db.SmallInteger, default=randint(0, 11), nullable=False)
    public_key = db.Column(db.String, nullable=False)


class Messages(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("profile.id"), nullable=False)
    sender = db.relationship("Profile", backref=db.backref("profile", uselist=False))
    receiver_id = db.Column(db.Integer, db.ForeignKey("profile.id"), nullable=False)
    receiver = db.relationship("Profile", backref=db.backref("profile", uselist=False))
    message = db.Column(db.String(20000), nullable=False)


class PasswordLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    used = db.Column(db.Boolean, default=False)
