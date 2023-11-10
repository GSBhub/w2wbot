# W2WBot
Simple discord bot for saying when your teams' next game at Wall2Wall is. Hard-coded for Sunday for right now, but if your game is consistently the same day you could probably change it for that.

## Installation
This requires the Discord API and the Beautiful Soup plugins for python, shown in the `requirements.txt` file.

## Basic Usage
To run, execute `python3 w2wbot.py TEAM_NAME DISCORD_API_TOKEN CHANNEL_ID`. I recommend storing the first three variables in a .env file and dumping them, for example, `source .env && python3 w2wbot.py "$TEAM_NAME" $TOKEN $CHANNEL --skip_first_week`. 

The bot is configured to immediately report your next team game, unless the current date is past the last posted date on your team's schedule page. If you pass in `--skip-first-week`, it'll start doing that after 7 days have passed from initial start. It will check daily for a new schedule posting and update if that is the next one. Might have to tweak this to be slightly smarter if Wall2Wall ever updates the entire schedule earlier.

In addition, if anyone posts a message in the chat with the tokens "time", "?" and one of "Sunday" or "Tomorrow", the bot will also query that. 
