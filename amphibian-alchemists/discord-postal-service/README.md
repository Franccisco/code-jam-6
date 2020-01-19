# Discord Postal Service

The DPS is a postal service for Discord. Don't want clear text messages on Discord's server? Then use the DPS to send it for you!

Table of Contents:
- How do you use it
- How does it work
- Integration with other city-based servers

-----
### How do you use it

The Discord Postal Service is a Discord server where users reside as "residents" of a Discord text chat. Each text chat resemebles a neighborhood or city that you will reside in.

You as a resident deliver the message to the post office. Other players as mail(wo)men deliver the message by dodging obstacles in order to ensure the message is safely delivered. If the mailrunner is stopped, the message is sent in clear text.

The encrypted message will be sent in the form of a link; inside the link is a plain website that will show the text to only that one user (using Discord oauth system so signup is not required).

The messages that are "caught" while being delivered will be sent in clear text in the server that the receiver's address (i.e. text chat) is located in.

----
### How does it work

Upon joining the server, you will be privately messaged a one-time link that will tell you a password. Save this password somewhere since we don't save it.

When sending a message, go to the dedicated website for sending it. Login using Discord. Fill out who the receiver will be by the format NAME#0000 and then write your message. Finally hit send.

Mailrunners also go to the website, report for duty, and start sending mail. You play the game and earn currency on the Discord server. If you fail by getting captured (or worse), then the message will be turned into clera-text and you will lose currency. Losing too much mail results in you getting fired. Repeated offenses can result in hanging (or the boot from the server).

The receiving end will be pinged a link in their neighborhood/dedicated chat. Upon entering the link, you can decrypt the message by filling in your password.

----
### Integration

There are plenty of city-based Discord servers that can be found here: https://disboard.org/servers/tag/city

The methodology of the "sending messages" part lies in the game. You can design the game by changing the methodlogy. Maybe the mailrunner is in a car and thugs try to steal packages. Maybe the mailrunner is on a horse and archers try to stop the runner.

The customizable portions is really endless. The best parts to customize is the game.

Deploying the Django web server can be done on PythonAnywhere. You can also use cookiecutter-django and a Raspberry Pi to deploy.
