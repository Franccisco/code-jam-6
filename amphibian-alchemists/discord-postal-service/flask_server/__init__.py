import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(PROJECT_DIR, ".env")

app = Flask(__name__)

app.debug = True
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "setsecretkeyinnewdotenvfile")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL"
) or "sqlite:///" + os.path.join(PROJECT_DIR, "app.db")

db = SQLAlchemy(app)
db.create_all()
migrate = Migrate(app, db)
with app.app_context():
    from .dps import views
