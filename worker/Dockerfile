FROM python:3.7

ADD common /common
ADD worker /worker

RUN pip3 install -r /worker/requirements.txt --no-cache-dir
CMD python3 -m worker
