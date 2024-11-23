# Naota
The Naota project is developed for academic popuses only. We do not hold ourselves responsable for the improper use of this code base. Please review the [Discord Developer Policy](https://discord.com/developers/docs/policies-and-agreements/developer-policy) and [Youtube API Terms of Service](https://developers.google.com/youtube/terms/api-services-terms-of-service) before moving forward.

> _"I'm a bot trying to be useful. Hope I'm not too buggy!"_ ~ Naota 2021 

This code base can run on Windows and Linux with proper [installation](#installation).

# Features and usage
Naota has the following Cogs:

- **MusicPlayer:** commands to stream youtube music.
- **Watchlist:** commands to keep track of series or movies.
- **Dev:** commands for general developer information and metrics.
- **Chess:** commands to solve chess puzzles - thanks to lichess for providing the [puzzle dataset](https://database.lichess.org/#puzzles)
- **Twitter:** commands to interact with the x/twitter API.

## For developers
Naota is built on top of [discord.py](https://discordpy.readthedocs.io/en/stable/) and the following APIs:

- [YouTube Data API](https://developers.google.com/youtube/v3)
- [X API](https://developer.x.com/en/products/x-api)

## Installation
#### Prerequisites:
- [Python 3.8+](https://www.python.org/)
- [ffmpeg](https://www.gyan.dev/ffmpeg/builds/) - For audio streaming
   
   odds are that you (like me) don't have this installed all ready. For a guide on how to do se we recomend [geeks for geeks tutorial](https://www.geeksforgeeks.org/how-to-install-ffmpeg-on-windows/)

- [cairo](https://www.cairographics.org/) - Mainly for svg to png convertions 

   in linux base distributions this is communly included, however in windows this is not the case. Precompiled binaries can be found [here](https://github.com/preshing/cairo-windows). The ddl should be on the system path.
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
TWITTER_KEY = "YOUR TWITTER KEY"
TWITTER_SECRET = "YOUR TWITTER SECRET"
TWITTER_BEARER = "YOUR TWITTER BEARER TOKEN"
TWITTER_ACCESS_TOKEN = "YOUR TWITTER ACCESS TOKEN"
TWITTER_ACCESS_TOKEN_SECRET = "YOUR TWITTER TOKEN SECRET"

COMMAND_PREFIX="/"
MAIN_COLOR="dark_blue"

LOG_LEVEL="DEBUG"

GIT_REPO="./.git"
DB_FILE_PATH="./naota.db"
PERMISSIONS_FILE_PATH="./permissions.json"
```
`YOUTUBE_TOKEN` and `CODEFORCES_TOKEN` are not actively being used, so asigning the to empty strings will probably be fine for now.

4. (Optional) Modify [the permissions.json]() file.

## The permissions JSON
Use it to allow per server or per user behaviour. The following permissions are available:

#### For entire cogs:
- Cog_MusicPlayer
- Cog_WatchlistCog
- Cog_Dev
- Cog_Chess
- Cog_Twitter

#### For individual commands:
- Command_Sync

To determine if a certain action is allowed, it must be included in either
the user permissions, the permissions of a group the user belongs to or the server
permissions from where the request was issued.

## Discord Scopes and Permissions
The application will request the following from your server:
#### Scopes:
- bot
- application.commands
#### Permissions:
- Send Messages
- Manage Messages
- Connect
- Speek
- Use Application Commands

The permision integer for them is `2150640640`.
