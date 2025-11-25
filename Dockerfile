FROM python:3-alpine

RUN apk update && apk add python3-dev gcc libc-dev

RUN pip3 install --no-cache --upgrade pip

RUN mkdir /w2wbot

COPY requirements.txt /w2wbot/

RUN pip3 install --no-cache -r /w2wbot/requirements.txt

COPY *.py /w2wbot/ 

ENTRYPOINT ["python3", "/w2wbot/w2wbot.py"]
