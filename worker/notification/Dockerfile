FROM python:3.7

ADD common /common
ADD worker/notification /worker/notification

RUN pip3 install -r /worker/notification/requirements.txt --no-cache-dir
CMD python3 -m worker.notification
