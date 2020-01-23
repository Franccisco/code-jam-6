import os

from dotenv import load_dotenv

from . import app, db, discord_client

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(PROJECT_DIR, ".env")

if __name__ == "__main__":
    load_dotenv(dotenv_path=env_path)
    app.run()
    db.create_all()
    discord_client.run(os.getenv("DISCORD_BOT_TOKEN"))
