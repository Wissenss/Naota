# Naota
I'm a bot trying to be useful. Hope I'm not too buggy!

The Naota project is developed for academic popuses only. We do not hold ourselves responsable for the improper use of this code base. Please review the [Discord Developer Policy](https://discord.com/developers/docs/policies-and-agreements/developer-policy) and [Youtube API Terms of Service](https://developers.google.com/youtube/terms/api-services-terms-of-service) before moving forward.

This code base can run on Windows and Linux with proper [setup](#setup).

## For developers
Naota is built on top of [discord.py](https://discordpy.readthedocs.io/en/stable/) and [YouTube Data API](https://developers.google.com/youtube/v3)

## Installation
#### Prerequisites:
1. [Python 3.8+](https://www.python.org/)
2. [ffmpeg](https://www.gyan.dev/ffmpeg/builds/) - For audio streaming
   
   odds are that you (like me) dont have this installed all ready. For a guide on how to do se we recomend [geeks for geeks tutorial](https://www.geeksforgeeks.org/how-to-install-ffmpeg-on-windows/)
#### Setup:
1. Get a local copy of the repository
```
git clone https://github.com/Wissenss/Naota.git
```
2. Install all necessary python modules
```
pip install -r requirements.txt
```
3. Create a new .env file inside the project folder and set it up as follows
```env
DISCORD_TOKEN="YOUR DISCORD TOKEN"
YOUTUBE_TOKEN="YOUR YOUTUBE API TOKEN"
CODEFORCES_TOKEN="YOUR CODEFORCES API TOKEN"

COMMAND_PREFIX="/"
MAIN_COLOR="dark_blue"

LOG_LEVEL="DEBUG"

DB_FILE_PATH="./naota.db"
```
`YOUTUBE_TOKEN`, `CODEFORCES_TOKEN` and `DB_FILE_PATH` are not actively being used, so not defining them will probably be fine for now but it's recommended to do so.
## Requirements
The application will request the following from your server:
#### Scopes:
1. bot
2. application.commands
#### Permissions:
1. Send Messages
2. Manage Messages
3. Connect
4. Speek
5. Use Application Commands

The permision integer for them is `2150640640`.