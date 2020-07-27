FROM python:3.7

ADD common /common
ADD worker/push_send /worker/push_send

RUN pip3 install -r /worker/push_send/requirements.txt --no-cache-dir
CMD python3 -m worker.push_send
