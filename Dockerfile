FROM python:3.7.4-slim

RUN apt-get update && apt-get install -y ffmpeg \
    && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN mkdir -p /usr/src/bot
WORKDIR /usr/src/bot

COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . /usr/src/bot

ENTRYPOINT ["python3", "-u", "telesco.py"]
