FROM python:3.7

ADD common /common
ADD worker/result /worker/result

RUN pip3 install -r /worker/result/requirements.txt --no-cache-dir
CMD python3 -m worker.result
