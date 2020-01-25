import os

from threading import Thread
from queue import Queue

from dotenv import load_dotenv

from . import app, db, discord_client

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(PROJECT_DIR, ".env")

DISCORD_PERMISSION_INT = 268658688


if __name__ == "__main__":
    # Setup queue
    # message_queue = Queue()
    # app.message_queue = message_queue
    # discord_client.message_queue = message_queue
    # Load Flask stuff
    load_dotenv(dotenv_path=env_path)
    app.run()
    db.create_all()
    # Begin Discord bot
    discord_client.run(os.getenv("DISCORD_BOT_TOKEN"))
    # discord_thread = Thread(target=discord_client.run, args=(os.getenv("DISCORD_BOT_TOKEN")))
    # discord_thread.start()
