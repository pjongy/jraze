FROM python:3.7

ADD common /common
ADD batch/notification /batch/notification

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r /batch/notification/requirements.txt --no-cache-dir
CMD python3 -m batch.notification
