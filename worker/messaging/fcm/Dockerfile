FROM python:3.7

ADD common /common
ADD worker/messaging/fcm /worker/messaging/fcm

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r /worker/messaging/fcm/requirements.txt --no-cache-dir
CMD python3 -m worker.messaging.fcm
