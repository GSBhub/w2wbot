FROM python:3-alpine

RUN mkdir /w2wbot

COPY *.py /w2wbot/ 

COPY requirements.txt /w2wbot/

RUN pip3 install --no-cache --upgrade pip

RUN pip3 install --no-cache -r /w2wbot/requirements.txt

ENTRYPOINT python3 /w2wbot/w2wbot.py "$TEAM_NAME" $DAY $TOKEN $CHANNEL 
