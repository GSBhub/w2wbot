FROM python:3-alpine

RUN pip3 install --no-cache --upgrade pip

RUN mkdir /w2wbot

COPY requirements.txt /w2wbot/

RUN pip3 install --no-cache -r /w2wbot/requirements.txt

COPY *.py /w2wbot/ 

ENTRYPOINT python3 /w2wbot/w2wbot.py "$TEAM_NAME" $TOKEN $CHANNEL $DAY $LOCATION
