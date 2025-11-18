#!/usr/bin/env python3
from w2w_getsched import getSchedule, getNextGame, getPreviousGame, dtoConv
from datetime import datetime, timedelta
import discord
from discord.ext import tasks
import asyncio
# nice ascii-based table
from table2ascii import table2ascii as t2a, PresetStyle
import os
from dotenv import load_dotenv

last_posted_message_time = None
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
channel = 0
schedule_channel = 0
schedule_message = None
team_name = ""
location = 0
game_day = 0

session_start = None

header=["Schedule", "Field", "Home", "Visitor", "Result"]

def schedule_message(teamName, location, force_message=False):
    global session_start

    msg = ""
    new_session = False
    sched = [_ for _ in getSchedule(teamName, location)]

    if len(sched) > 0:
        msg = t2a(
            header=header,
            body=sched,
            style=PresetStyle.thin_compact
            )

        sched_start = dtoConv(sched[0][0][4:])
        if sched_start.date() != session_start.date():
            new_session = True
            session_start = sched_start
    return msg, new_session
    

def next_game_message(teamName, location, force_message=False):

    nextGame = getNextGame(teamName, location)
    msg = ""

    if nextGame:
        gameTime = nextGame[0]
        dto = dtoConv(gameTime[4:])
        field = nextGame[1]
        isHome = (nextGame[2] == teamName.upper())
        opponent = nextGame[3] if isHome else nextGame[2]
        msg = f"{teamName.upper()}'s next game is {gameTime} {dto.year} against {opponent} on {field}."
        msg += f"\n{teamName.upper()} is the home team." if isHome else f"\n{teamName.upper()} is the away team."
    
    if msg == "" and force_message:
        msg = "Wall2Wall hasn't posted the next game yet!"

    return msg


def prev_game_message(teamName, location, force_message=False):
    prevGame = getPreviousGame(teamName, location)
    msg = ""
    
    if prevGame:
        gameTime = prevGame[0]
        dto = dtoConv(gameTime[4:])
        field = prevGame[1]
        isHome = (prevGame[2] == teamName.upper())
        opponent = prevGame[3] if isHome else prevGame[2]
        msg = f"{teamName.upper()}'s previous game was {gameTime} {dto.year} against {opponent} on {field}."
        msg += f"\n{teamName.upper()} was the home team." if isHome else f"\n{teamName.upper()} was the away team."
        msg += f"\nThe score of that game was (Home - Away): {prevGame[4]}"

    if msg == "" and force_message:
        msg = f"{teamName} has not had a game yet this session!"

    return msg

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    nextGameMsg.start()
    getSchedMsg.start()

# check every day to see if we should post the message
@tasks.loop(hours=24)
async def nextGameMsg():
    global team_name
    global location
    global channel
    global last_posted_message_time
    print(f"Retrieving channel {channel}...")
    message_channel = client.get_channel(channel)
    msg = next_game_message(team_name, location)
    if msg != "":
        # determine if we should post
        # criteria: DOW you care about (ex 7, for sunday)
        # and last message time 
        # last message time .weekday() - weekday_of_game < 0?
        # alternatively, post a message if it's been about a week since we last posted
        if last_posted_message_time == None or ((datetime.now().weekday() - last_posted_message_time.weekday()) < 0) or ((datetime.now().weekday() - game_day) < 0):
            
            await message_channel.send(msg)
            last_posted_message_time = datetime.now()


# check daily to see if the scores have updated, or if a new schedule is posted
@tasks.loop(hours=24)
async def getSchedMsg():
    global team_name
    global location
    global schedule_channel
    global schedule_message
    print(f"Retrieving channel {channel}...")
    message_channel = client.get_channel(schedule_channel)
    msg, new_session = schedule_message(team_name, location)

    if msg != "":
        if new_session:
            schedule_message = await ctx.send(msg) 
        else: # edit the previous message instead of just sending the same schedule
            schedule_message = await schedule_mesage.edit(content=msg)


@client.event
async def on_message(message):
    global team_name
    global location
    if message.author == client.user:
        return

    if "play" in message.content.lower() and "?" in message.content and ("when" in message.content.lower() or "tomorrow" in message.content.lower()):
        await message.channel.send(schedule_message(team_name, location, True))

days_of_week = ["Monday", "Tuesday", "Wedneday", "Thursday", "Friday", "Saturday", "Sunday"]

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    
    # 
    parser.add_argument("-n", "--team_name", help="Team Name")
    parser.add_argument("-o", "--token", help="Discord API Token")
    parser.add_argument("-c", "--channel", type=int, help="Channel to send game reminders to")
    parser.add_argument("-l", "--location", type=int, help="Team location value (check team schedule website, it's the number in the URL)")

    parser.add_argument("--schedule_channel", type=int, help="Channel to send the full schedule to, if different than channel")
    parser.add_argument("-d", "--day", default="Thursday", type=lambda s : s[0].upper() + s[1:].lower(), choices=days_of_week, help="Day of the week to post game times on, if available. Will delay until later if the game time hasn't been posted yet.")
    parser.add_argument("-s", "--skip_first_week", default=False, action="store_true", help="Don't send the message during the first week this bot is on.")
    parser.add_argument("-t", "--test", action="store_true", help="Print messages and exit without connecting to Discord.")
    parser.add_argument("-a", "--session_start", type=lambda s: dtoConv(s), help="Sessionstart date (avoids sending the schedule if set). Format is \"MM/DD HH:MM (am/pm)\"")

    args = parser.parse_args()

    load_dotenv()

    team_name = args.team_name if args.team_name else os.getenv('TEAM_NAME')
    token = args.token if args.token else os.getenv('TOKEN')
    location = args.location if args.location else os.getenv('LOCATION')
    channel = args.channel if args.channel else os.getenv('CHANNEL')
    
    err = False

    if team_name is None:
        print("Set the \"TEAM_NAME\" environment variable or provide a team name with --team_name")
        err = True

    if token is None:
        print("Set the \"TOKEN\" environment variable or provide a team name with --token")
        err = True 

    if location is None:
        print("Set the \"LOCATION\" environment variable (integer) or provide a location with --location")
        err = True
    else:
        location = int(location)

    if channel is None:
        print("Set the \"CHANNEL\" environment variable (integer) or provide a location with --channel")
        err = True
    else:
        channel = int(channel)
        
    if err:
        parser.print_usage()
        parser.exit()

    if args.schedule_channel:
        schedule_channel = args.schedule_channel
    else:
        schedule_channel = channel

    game_day = days_of_week.index(args.day)

    if args.skip_first_week:
        last_posted_message_time = datetime.now()
    else:
        last_posted_message_time = None

    if args.session_start:
        session_start = args.session_start
    else:
        session_start = datetime.now()

    if args.test:
        print(schedule_message(team_name, location))
        print(prev_game_message(team_name, location))
        print(next_game_message(team_name, location))

        # query server + display channels too
        
        bot = discord.Client(intents=discord.Intents.default())

        @bot.event
        async def on_ready():
            text_channel_list = []
            for guild in bot.guilds:
                for channel in guild.text_channels:
                    text_channel_list.append(channel)
                    print(channel, guild.name)

        print("Attempting to query channel names/IDs using token/channel")
        try:
            bot.run("TOKEN")
        except:
            print("Query failed.")


    else:
        client.run(token)
