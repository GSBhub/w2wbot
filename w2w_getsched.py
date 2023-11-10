#!/usr/bin/env python3
from requests_html import HTMLSession
import json
import urllib
from bs4 import BeautifulSoup
import argparse

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

    # this is painful but the website gives me a 500 error if I don't have it
    headers = {"host": "www.letsplaysoccer.com",
        "Connection": "keep-alive",
        "sec-ch-ua": "\"Chromium\";v=\"119\", \"Not?A_Brand\";v=\"24\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "Linux",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Accept-Language": "en-US,en;q=0.9"
    }

    req = urllib.request.Request(w2wSchedUrl, headers=headers)
    request = urllib.request.urlopen(req)
    if (request.getcode() == 200):
        teamData = request.read().decode('utf-8')

    return teamData


def getSchedule(teamName, location):
    
    teamData = getTeamData(teamName, location)
    soup = BeautifulSoup(teamData, "html.parser")
    last_row = soup.find_all("tr")[-1] # this works fine
    row_contents = [element.text for element in last_row]
    return row_contents

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("team_name", help="Team name to query.")
    args = parser.parse_args()
    print(getSchedule(args.team_name))
