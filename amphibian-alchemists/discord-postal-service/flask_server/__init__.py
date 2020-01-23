import os

import discord
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, orm

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(PROJECT_DIR, ".env")

app = Flask(__name__)

app.debug = True
if app.debug:
    root_url = "http://localhost:5000"
else:
    root_url = "https://pythonanywhere.com"
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "setsecretkeyinnewdotenvfile")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
sqlite_path = "sqlite:///" + os.path.join(PROJECT_DIR, "app.db")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL"
) or sqlite_path

# Recaptcha
app.config['RECAPTCHA_USE_SSL'] = False
app.config['RECAPTCHA_PUBLIC_KEY'] = os.getenv("RECAPTCHA_PUBLIC_KEY")
app.config['RECAPTCHA_PRIVATE_KEY'] = os.getenv("RECAPTCHA_PRIVATE_KEY")
app.config['RECAPTCHA_OPTIONS'] = {'theme': 'black'}

# Database
db = SQLAlchemy(app)
db.create_all()
migrate = Migrate(app, db)
engine = create_engine(sqlite_path, echo=app.debug)
db_session = orm.Session(engine)

# Setting up Discord Bot
discord_client = discord.Client()
DISCORD_PERMISSION_INT = 268658688

with app.app_context():
    from .dps import views
