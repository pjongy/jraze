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

### Push worker
#### Run worker (FCM)
```
$ export PUSH_WORKER__FIREBASE__SERVER_KEY={..fcm server key..}
$ export PUSH_WORKER__REDIS__HOST={...}
$ export PUSH_WORKER__REDIS__PASSWORD={...}
$ python3 -m worker.push.fcm
```

#### Run worker with docker-compose in local
```
$ export PUSH_WORKER__FIREBASE__SERVER_KEY={..fcm server key..}
$ docker-compose -f local-docker-compose.yml up -d push-worker
```

### Result worker
#### Run worker
```
$ export RESULT_WORKER__REDIS__HOST={...}
$ export RESULT_WORKER__REDIS__PASSWORD={...}
$ export RESULT_WORKER__MYSQL__HOST={...}
$ export RESULT_WORKER__MYSQL__USER={...}
$ export RESULT_WORKER__MYSQL__PASSWORD={...}
$ python3 -m worker.result
```

#### Run worker with docker-compose in local
```
$ docker-compose -f local-docker-compose.yml up -d result-worker
```

### Notification worker
#### Run worker
```
$ export NOTIFICATION_WORKER__REDIS__HOST={...}
$ export NOTIFICATION_WORKER__REDIS__PASSWORD={...}
$ export NOTIFICATION_WORKER__MYSQL__HOST={...}
$ export NOTIFICATION_WORKER__MYSQL__USER={...}
$ export NOTIFICATION_WORKER__MYSQL__PASSWORD={...}
$ python3 -m worker.notification
```

#### Run worker with docker-compose in local
```
$ docker-compose -f local-docker-compose.yml up -d notification-worker
```

## API server

### Run server
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


## Sequence

[API server] -> [Notification worker] -> [Push worker] -> [Result worker]