from w2w_getsched import getSchedule
from datetime import datetime, timedelta
import discord
from discord.ext import tasks
import asyncio

last_posted_message_time = None
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
channel = 0
team_name = ""
location = 0
game_day = 0

def schedule_message(teamName, location, force_message=False):
    teamSchedule = getSchedule(teamName, location)
    msg = ""

    if teamSchedule:
        now = datetime.now()
        gameTime = teamSchedule[0]
        dto = datetime.strptime(gameTime, "Sun %m/%d %H:%M %p")

        # set year accordingly
        dto = dto.replace(year=now.year if dto.month >= now.month else yearnow.year+1)
        
        if dto.date() > now.date():
            field = teamSchedule[1]
            isHome = (teamSchedule[2] == teamName.upper())
            opponent = teamSchedule[3] if isHome else teamSchedule[2]
            msg = f"{teamName.upper()}'s next game is {gameTime} {dto.year} against {opponent} on {field}."
            msg += f"\n{teamName.upper()} is the home team." if isHome else f"\n{teamName.upper()} is the away team."
    
    if msg == "" and force_message:
        msg = "Wall2Wall hasn't posted the next game yet!"

    return msg


@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    cronMsg.start()

@tasks.loop(hours=24)
async def cronMsg():
    global team_name
    global location
    global channel
    global last_posted_message_time
    print(f"Retrieving channel {channel}...")
    message_channel = client.get_channel(channel)
    msg = schedule_message(team_name, location)
    if msg != "":
        # determine if we should post
        # criteria: DOW you care about (ex 7, for sunday)
        # and last message time 
        # last message time .weekday() - weekday_of_game < 0?
        # alternatively, post a message if it's been about a week since we last posted

        if last_posted_message_time == None or ((datetime.now().weekday() - last_posted_message_time.weekday()) < 0) or ((datetime.now().weekday() - game_day) < 0):
            
            await message_channel.send(msg)
            last_posted_message_time = datetime.now()

@client.event
async def on_message(message):
    global team_name
    global location
    if message.author == client.user:
        return

    if "play" in message.content.lower() and "?" in message.content and ("when" in message.content.lower() or "tomorrow" in message.content.lower()):
        await message.channel.send(schedule_message(team_name, location, True))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("team_name", help="Team Name")
    parser.add_argument("token", help="Discord API Token")
    parser.add_argument("channel", type=int, help="Channel to talk in")
    parser.add_argument("game_day", type=int, help="Day of week, from 1 (Monday) to 7 (Sunday) the game you care about is on.")
    parser.add_argument("location", type=int, help="Team location value (check website, it's the number)")
    parser.add_argument("--skip_first_week", default=False, action="store_true", help="Don't send the message during the first week this bot is on.")

    args = parser.parse_args()
    
    team_name = args.team_name
    token = args.token 
    location = args.location
    channel = args.channel
    game_day = args.game_day
    if args.skip_first_week:
        last_posted_message_time = datetime.now()
    else:
        last_posted_message_time = None

    client.run(token)
