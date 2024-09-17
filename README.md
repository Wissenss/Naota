# Naota
The Naota project is developed for academic popuses only. We do not hold ourselves responsable for the improper use of this code base. Please review the [Discord Developer Policy](https://discord.com/developers/docs/policies-and-agreements/developer-policy) and [Youtube API Terms of Service](https://developers.google.com/youtube/terms/api-services-terms-of-service) before moving forward.

> _"I'm a bot trying to be useful. Hope I'm not too buggy!"_ ~ Naota 2021 

This code base can run on Windows and Linux with proper [setup](#setup).

# Features and usage
Naota has the following Cogs:

1. MusicPlayer: commands to stream youtube music.
2. Watchlist: commands to keep track of series or movies.

## For developers
Naota is built on top of [discord.py](https://discordpy.readthedocs.io/en/stable/) and [YouTube Data API](https://developers.google.com/youtube/v3).

## Installation
#### Prerequisites:
1. [Python 3.8+](https://www.python.org/)
2. [ffmpeg](https://www.gyan.dev/ffmpeg/builds/) - For audio streaming
   
   odds are that you (like me) don't have this installed all ready. For a guide on how to do se we recomend [geeks for geeks tutorial](https://www.geeksforgeeks.org/how-to-install-ffmpeg-on-windows/)
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
`YOUTUBE_TOKEN` and `CODEFORCES_TOKEN` are not actively being used, so not defining them will probably be fine for now but it's recommended to do so.

4. (Optional) Create a permissions.json, (use to define per server or per user permissions). The file follows this structure:
```json
{
   "Users" : {
      "discordMemberId" : {
         "Alias" : A STRING VALUE FOR REFERENCE ONLY, AS YOU PROBABLY WONT IDENTIFY A CERTAIN USER BY IT'S DISCORD ID
         "Groups" : [],
         "Permissions": []
      }
   },
   "Servers" : {
      "discordServerId": {
         "Alias" : ANOTHER STRING VALUE FOR REFERENCE
         "Groups" : [],
         "Permissions" : []
      }
   },
   "Groups" : [
      "groupName" : {
         "Permissions" : []
      }
   ]
}
```
The following permissions are available:
1. MusicPlayerCog: Access to music player commands.
2. WatchlistCog: Access to watchlist commands.

To determine if a certain permission is valid, it must be included in either
the user permissions, the permissions of a group the user belongs to or the server
permissions from where the request was issued.

## Discord Scopes and Permissions
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
