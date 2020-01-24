import os
from threading import Thread
from queue import Queue, Empty

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

with app.app_context():
    queue = Queue()
    from .dps import views

# Setting up Discord Bot
# queue = Queue()
discord_client = discord.Client()

"""
from threading import Thread
from queue import Queue, Empty
import time, random

q = Queue()

def func1():
    while True:
        for _ in range(10):
            q.put(random.randint(0,1000))
        q.join()

def func2():
    while True:
        try:
            i = q.get()
            print('Processing ', i)
            time.sleep(1)
            q.task_done()
        except Empty:pass

if __name__ == '__main__':
    t1 = Thread(target=func1)
    t2 = Thread(target=func2)
    t1.start()
    t2.start()
    
try:
  item = q.get()
  # do stuff
  q.task_done()
except Empty:
  # queue is empty, do other stuff
  pass
  
q.get(block=False)
"""
