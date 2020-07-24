FROM python:3.7

ARG WORKER_COUNT
ENV WORKER_COUNT ${WORKER_COUNT}

ADD apiserver /apiserver
ADD common /common

RUN pip3 install -r /apiserver/requirements.txt --no-cache-dir
CMD gunicorn apiserver.application:application --bind 0.0.0.0:8080 --worker-class aiohttp.GunicornWebWorker --workers=$WORKER_COUNT --logger-class common.logger.gunicorn.CustomLogger --access-logfile -
EXPOSE 8080