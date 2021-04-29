FROM python:3.7

ADD common /common
ADD worker/messaging/apns /worker/messaging/apns

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r /worker/messaging/apns/requirements.txt --no-cache-dir
CMD python3 -m worker.messaging.apns
