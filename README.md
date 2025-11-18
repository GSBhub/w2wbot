# W2WBot
Simple discord bot for saying when your teams' next game at Wall2Wall/LetsPlaySoccer is. Uses some web scraping to parse the website, so prone to breaking if they ever update layouts significantly.


## Installation

Recommended install is in a virtualenv (`python3 -m venv .venv && source .venv/bin/activate` or `mkvirtualenv w2wbot && workon w2wbot`)

`pip3 install -r requirements.txt`


## Basic Usage
To run, execute `python3 w2wbot.py --team_name TEAM_NAME --token TOKEN --channel CHANNEL --location LOCATION`. I recommend storing the first four variables in a .env file, w2wbot will attempt to use `dotenv` to load them from that if they are not provided via the commandline. (Environment variables are `TEAM_NAME`, `CHANNEL`, `TOKEN`, and `LOCATION`. `CHANNEL` is expected to be an integer for the discord channel that is being posted in, `TOKEN` is the discord API token, `TEAM_NAME` is the name of the team to query, and `LOCATION` is the numeric location code that LetsPlaySoccer uses to identify its locations (this can be found in the url corresponding to your team).

The bot is configured to immediately report your next team game, unless the current date is past the last posted date on your team's schedule page. If you pass in `--skip-first-week`, it'll start doing that after 7 days have passed from initial start. It will check daily for a new schedule posting and update if that is the next one. Might have to tweak this to be slightly smarter if Wall2Wall ever updates the entire schedule earlier.

The bot is also configured to report the full team schedule posted thus far as a table, which will also have the information for previous game times available.

In addition, if anyone posts a message in the chat with the tokens "time", "?" and one of "Sunday" or "Tomorrow", the bot will manually do its query for game time. 

## Dockerfile
`source .env && docker build -t w2wbot . && docker run w2wbot`

## Docker-compose
Create your `.env` and run `docker-compose up`.
