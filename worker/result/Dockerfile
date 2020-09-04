FROM python:3.7

ADD common /common
ADD worker/result /worker/result

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r /worker/result/requirements.txt --no-cache-dir
CMD python3 -m worker.result
