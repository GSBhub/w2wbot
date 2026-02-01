#!/usr/bin/env python3
import json
import urllib.request
from bs4 import BeautifulSoup
import argparse
from datetime import datetime

def getTeamId(teamName, location):
    teamId = None
    teamUri = teamName.replace(" ", "%20")
    w2w_apiserv = f"https://lps-api-prod.lps-test.com/teams/search_teams?name={teamUri}&facility_id={location}"
    req = urllib.request.urlopen(w2w_apiserv)
    if (req.getcode() == 200):
        teamId = json.loads(req.read())[0]['UTeamID']
    
    return teamId
        

def getTeamData(teamName, location):
    teamData = None
    teamId = getTeamId(teamName, location)

    if teamId:
        w2wSchedUrl = f"https://www.letsplaysoccer.com/{location}/teamSchedule/{teamId}?lang=en"

    # formerly had:        "sec-ch-ua": "\"Chromium\";v=\"119\", \"Not?A_Brand\";v=\"24\"",
    #        "sec-ch-ua-platform": "Linux",
    #         "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",

    # this is painful but the website gives me a 500 error if I don't have it
    headers = {"host": "www.letsplaysoccer.com",
        "Connection": "keep-alive",
        "sec-ch-ua-mobile": "?0",
        "Upgrade-Insecure-Requests": "1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Cookie": "lang=en",
        "DNT" : "1",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Accept-Language": "en-US,en;q=0.5",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0"
    }

    req = urllib.request.Request(w2wSchedUrl, headers=headers)
    request = urllib.request.urlopen(req)
    if (request.getcode() == 200):
        teamData = request.read().decode('utf-8')

    return teamData


def getSchedule(teamName, location):
    
    teamData = getTeamData(teamName, location)
    soup = BeautifulSoup(teamData, "html.parser")
    # return all the rows/schedules
    for row in soup.find_all("tr")[1:]: # ignore the table header
        row_contents = [element.text for element in row]
        yield row_contents


# converts ate from the format string "%m/%d %H %M %p"
# to use with the w2w strings, just carve off the first 4 chars (Day + " ")
def dtoConv(conv_date):
    now = datetime.now()

    dto = datetime.strptime(conv_date, "%m/%d %H:%M %p")
    
    # push the year forward 1 for schedules that run between EOY and BOY
    dto = dto.replace(year=now.year + 1 if (dto.month == 1 and now.month == 12) else now.year)
    
    return dto


# Get the previous game time played by this team at the given location
# starting from the date provided
# if no games exist before that time, None is returned.
def getPreviousGame(teamName, location, ftime=None):
    if ftime is None:
        ftime = datetime.now()

    # grab list to reverse 
    schedule = [_ for _ in getSchedule(teamName, location)]

    for row in reversed(schedule):
        # first 4 chars are DAY and space
        dto = dtoConv(row[0][4:])
        if dto.date() < ftime.date(): # game is before "from"
            return row
    return None


# Get the next game time played by this team at the given location
# starting from the date provided
def getNextGame(teamName, location, ftime=None):
    if ftime is None:
        ftime = datetime.now()

    for row in getSchedule(teamName, location):
        dto = dtoConv(row[0][4:])
        print(f"dto date {dto.date()} vs ftime date: {ftime.date()}")

        if dto.date() > ftime.date(): # game is after "from"
            return row
    return None

if __name__ == '__main__':
    parser = argparse.ArgumentParser("Return the next available game from the provided team.")
    parser.add_argument("team_name", help="Team name to query.")
    parser.add_argument("location", type=int, help="Team int to query. To find, query the w2w api.")
    parser.add_argument("-d", "--date", type=lambda s: dtoConv(s), help="From date, in the form \"MM/DD HH:MM (am/pm)\"")
    parser.add_argument("-p", "--prev", action="store_true", help="Get previous game instead of next game")

    args = parser.parse_args()
    func = getNextGame
    if args.prev:
        func = getPreviousGame

    print(func(args.team_name, args.location, ftime=args.date))
