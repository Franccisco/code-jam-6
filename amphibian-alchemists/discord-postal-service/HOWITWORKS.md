# How to set this up

You're going to need a Discord Devloper account, i.e. just go to the Discord Developer portal and sign-in with your Discord account.

Create a new application. We've called it Discord Postal Service. Copy your Client ID and Client Secret. Store them inside your new file called .env file. In deployment, you'll want to simply store them as environment variables and perhaps even remove dotenv entirely.

When that's done, clone this repository. In a terminal/cmd, go to the `flask_server` directory and do the following commands:

```
flask db init
flask db migrate
flask db upgrade
```

If you want to add more models, then do `db migrate && db upgrade`. Yoom is also not familiar with Flask, so that may not be all as there was mention of Flask-migrate's limitations.