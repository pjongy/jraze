FROM python:3.7

ADD common /common
ADD worker/push/fcm /worker/push/fcm

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r /worker/push/fcm/requirements.txt --no-cache-dir
CMD python3 -m worker.push.fcm
