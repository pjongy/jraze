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

## Quick start (on local)

### Pre-requisites
- docker >= 19.03.8
- docker-compose >= 1.25.5
- python >= 3.7

```
------- Select FCM API version
| $ export PUSH_WORKER__FCM__LEGACY__SERVER_KEY={..fcm server key..}
| $ export PUSH_WORKER__FCM__CLIENT=legacy
-------
| $ export PUSH_WORKER__FCM__V1__KEY_FILE_NAME={..fcm service account key path..}
| $ export PUSH_WORKER__FCM__V1__PROJECT_ID={..fcm project id..}
| $ export PUSH_WORKER__FCM__CLIENT=v1
-------
------- Select APNs authorization method
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


## Project structure
```
/
  /apiserver
  /worker
    /messaging
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
  - Client for update notifications' sent result

- Messaging worker (Push worker)
  ---
  - Client for send push message to each send platform like: FCM, APNs
  - Publish job for 'Result worker' to update notification sent result (success / failed)


### Sequence
```
[API server] -> [Notification worker] -> [Push worker]
                        ^---------------------|
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
