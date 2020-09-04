FROM python:3.7

ADD common /common
ADD worker/notification /worker/notification

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r /worker/notification/requirements.txt --no-cache-dir
CMD python3 -m worker.notification
