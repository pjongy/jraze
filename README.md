# Pusher

## Pre-requisites
- docker >= 19.03.8
- docker-compose >= 1.25.5
- python >= 3.7

## Quick start (on local)
```
$ export PUSH_WORKER__FIREBASE__SERVER_KEY={..fcm server key..}
$ docker-compose -f local-docker-compose.yml up -d
```

## Worker

### Run worker
```
$ export PUSH_WORKER__FIREBASE__SERVER_KEY={..fcm server key..}
$ export PUSH_WORKER__REDIS__PASSWORD={...}
$ python3 -m worker
```

### Run worker with docker-compose in local
```
$ export PUSH_WORKER__FIREBASE__SERVER_KEY={..fcm server key..}
$ docker-compose -f local-docker-compose.yml up -d push-worker
```

## API server

### Run worker
```
$ export API_SERVER__MYSQL__HOST = {...}
$ export API_SERVER__MYSQL__USER = {...}
$ export API_SERVER__MYSQL__PASSWORD = {...}
$ export API_SERVER__REDIS__HOST = {...}
$ export API_SERVER__REDIS__PASSWORD = {...}
$ python3 -m apiserver
```

### Run worker with docker-compose in local
```
$ docker-compose -f local-docker-compose.yml up -d api-server
```