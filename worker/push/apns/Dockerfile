FROM python:3.7

ADD common /common
ADD worker/push/apns /worker/push/apns

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r /worker/push/apns/requirements.txt --no-cache-dir
CMD python3 -m worker.push.apns
