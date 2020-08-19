<div align="center">
  <br/>
  <img src="./docs/image/jraze-logo.png" width="400"/>
  <br/>
  <br/>
  <p>
    Installable push sending service which can control push targets  <br/>
    with their properties by notification's conditions.  
  </p>
  <p>
    <a href="https://github.com/pjongy/jraze/blob/master/LICENSE">
      <img src="https://img.shields.io/badge/license-MIT-blue.svg"/>
    </a>
  </p>
</div>

---

## Pre-requisites
- docker >= 19.03.8
- docker-compose >= 1.25.5
- python >= 3.7

## Quick start (on local)
```
------- Select FCM API version
| $ export PUSH_WORKER__FCM__LEGACY__SERVER_KEY={..fcm server key..}
| $ export PUSH_WORKER__FCM__CLIENT=legacy
-------
| $ export PUSH_WORKER__FCM__V1__KEY_FILE_NAME={..fcm service account key path..}
| $ export PUSH_WORKER__FCM__V1__PROJECT_ID={..fcm project id..}
| $ export PUSH_WORKER__FCM__CLIENT=v1
-------
------- Select P8 file(latest) for authentication
| $ export PUSH_WORKER__APNS__P8_CERT__FILE_NAME={..apple apns p8 file path..}
| $ export PUSH_WORKER__APNS__P8_CERT__KEY_ID={..apple apns key_id..}
| $ export PUSH_WORKER__APNS__P8_CERT__TEAM_ID={..apple team_id..}
| $ export PUSH_WORKER__APNS__P8_CERT__TOPIC={..apple product bundle id..}
| $ export PUSH_WORKER__APNS__CERT_TYPE=p8
-------
| $ export PUSH_WORKER__APNS__PEM_CERT__FILE_NAME={..apple apns pem file path..}
| $ export PUSH_WORKER__APNS__CERT_TYPE=pem
-------
$ docker-compose -f local-docker-compose.yml up -d
```

## Worker

### Push worker
#### Run worker (FCM)
```
$ export ENV=dev
------- Select FCM API version
| $ export PUSH_WORKER__FCM__LEGACY__SERVER_KEY={..fcm server key..}
| $ export PUSH_WORKER__FCM__CLIENT=legacy
-------
| $ export PUSH_WORKER__FCM__V1__KEY_FILE_NAME={..fcm service account key path..}
| $ export PUSH_WORKER__FCM__V1__PROJECT_ID={..fcm project id..}
| $ export PUSH_WORKER__FCM__CLIENT=v1
-------
$ export PUSH_WORKER__REDIS__HOST={...}
$ export PUSH_WORKER__REDIS__PASSWORD={...}
$ python3 -m worker.push.fcm
```

#### Run worker (APNs)
```
$ export ENV=dev
------- Select P8 file(latest) for authentication
| $ export PUSH_WORKER__APNS__P8_CERT__FILE_NAME={..apple apns p8 file path..}
| $ export PUSH_WORKER__APNS__P8_CERT__KEY_ID={..apple apns key_id..}
| $ export PUSH_WORKER__APNS__P8_CERT__TEAM_ID={..apple team_id..}
| $ export PUSH_WORKER__APNS__P8_CERT__TOPIC={..apple product bundle id..}
| $ export PUSH_WORKER__APNS__CERT_TYPE=p8
-------
| $ export PUSH_WORKER__APNS__PEM_CERT__FILE_NAME={..apple apns pem file path..}
| $ export PUSH_WORKER__APNS__CERT_TYPE=pem
-------
$ export PUSH_WORKER__REDIS__HOST={...}
$ export PUSH_WORKER__REDIS__PASSWORD={...}
$ python3 -m worker.push.fcm
```

### Result worker
#### Run worker
```
$ export ENV=dev
$ export RESULT_WORKER__REDIS__HOST={...}
$ export RESULT_WORKER__REDIS__PASSWORD={...}
$ export RESULT_WORKER__MYSQL__HOST={...}
$ export RESULT_WORKER__MYSQL__USER={...}
$ export RESULT_WORKER__MYSQL__PASSWORD={...}
$ python3 -m worker.result
```

### Notification worker
#### Run worker
```
$ export ENV=dev
$ export NOTIFICATION_WORKER__REDIS__HOST={...}
$ export NOTIFICATION_WORKER__REDIS__PASSWORD={...}
$ export NOTIFICATION_WORKER__MYSQL__HOST={...}
$ export NOTIFICATION_WORKER__MYSQL__USER={...}
$ export NOTIFICATION_WORKER__MYSQL__PASSWORD={...}
$ python3 -m worker.notification
```

## API server

### Run server
```
$ export ENV=dev
$ export API_SERVER__MYSQL__HOST={...}
$ export API_SERVER__MYSQL__USER={...}
$ export API_SERVER__MYSQL__PASSWORD={...}
$ export API_SERVER__REDIS__HOST={...}
$ export API_SERVER__REDIS__PASSWORD={...}
$ python3 -m apiserver
```


## Project structure
```
/
  /apiserver
  /worker
    /push
      /fcm
    /result
    /notification
```

- API server
  ---
  - Endpoint for client can attach through REST API
  - Take roles about register device/notification
  - Also it shows device's event for notification
  - Publish job for 'Notification worker'

- Notification worker
  ---
  - Find devices comfort notification's condition and publish job for 'Push worker'

- Push worker
  ---
  - Client for send push message to each send platform like: FCM, APNs
  - Publish job for 'Result worker' to update notification sent result (success / failed)

- Result worker
  ---
  - Client for update notifications' sent result

### Sequence
```
[API server] -> [Notification worker] -> [Push worker] -> [Result worker]
```

## Trouble shooting

### FCM

-  FCM worker can't send notification with 403

    ```json
    {"code": 403, "message": "The caller does not have permission", "status": "PERMISSION_DENIED"}}
    ```
    You should set permission "cloudmessaging.messages.create"

### APNs

- Extract PEM file from *.p12
    ```
    openssl pkcs12 -in {P12 FILE} -out {EXPORTED PEM FILE} -nodes -clcerts
    ```
