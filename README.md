# Pusher

## Worker

## Pre-requisites
- docker >= 19.03.8
- docker-compose >= 1.25.5
- python >= 3.7


### Run worker
```
$ export PUSH_WORKER__FIREBASE__SERVER_KEY={..fcm server key..}
$ export PUSH_WORKER__REDIS__PASSWORD={...}
$ python3 -m worker
```

### Run worker with docker-compose in local
```
$ export PUSH_WORKER__FIREBASE__SERVER_KEY={..fcm server key..}
$ docker-compose -f local-docker-compose.yml up -d
```