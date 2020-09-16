FROM python:3.7

ADD common /common
ADD worker/messaging /worker/messaging

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r /worker/messaging/requirements.txt --no-cache-dir
CMD python3 -m worker.messaging
