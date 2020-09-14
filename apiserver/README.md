# jraze API server

## Pre-requisites
- python >= 3.7

## Endpoint
### Device management

#### Enums
```python
# common/structure/enum.py
class DevicePlatform(enum.IntEnum):
    UNKNOWN = 0
    ANDROID = 1
    IOS = 2
    WEB = 3

class SendPlatform(enum.IntEnum):
    UNKNOWN = 0
    FCM = 1
    APNS = 2
```
```python
# common/model/notification.py
class NotificationStatus(enum.IntEnum):
    DRAFT = 0
    LAUNCHED = 1
    SENT = 2
    ERROR = 3
    DELETED = 4
```

```python
# apiserver/repository/device.py
available_join_types = {'OR', 'AND'}
operators = {
    'int_eq': VALUE_INT,
    'int_gt': f'{VALUE_INT}__gt',
    'int_gte': f'{VALUE_INT}__gte',
    'int_lt': f'{VALUE_INT}__lt',
    'int_lte': f'{VALUE_INT}__lte',
    'str_exists': f'{VALUE_STR}__contains',
    'str_eq': VALUE_STR,
}
```

#### API specs

- /devices
  - /{external_id} *GET*
    - purpose: Fetch selected device information
    - request: `Empty`
    - response:
        ```
        {
          "success": ...,
          "result": {
            "id": ..sequential number..,
            "external_id": ...device id...,
            "push_token": ...,
            "send_platform": ...,
            "device_platform": ...,
            "created_at": ...,
            "modified_at": ...,
            "device_properties": [ {...key...: ...value...}, ... ]
          },
          "reason": ...,
        }
        ```

  - / *POST*
    - purpose: Create device
    - request:
        ```
        {
          "push_token": "{{PUSH_TOKEN}}",
          "send_platform": 1,  # FCM
          "device_platform": 1  # ANDROID
        }
        ```
    - response: `Same as /devices/{external_id} GET response`

  - / *PUT*
    - purpose: Update or Create device information
        ```
        {
          "external_id": ... classifier from external accesss (set up manually)...[str]
          "push_token": "{{PUSH_TOKEN}}",
          "send_platform": 1,  # FCM
          "device_platform": 1  # ANDROID
        }
        ```

  - /{external_id}/properties/:add *POST*
    - purpose: Add device's properties that can be filtered by condition clause
    - request:
        ```
        {
          "properties": [
            {"key": "k", "value": "v"},  # Request str type (quoted) value means key k's type is "string"
            {"key": "k", "value": 1}  # Request int type (not-quoted) value means key k's type is "int"
          ]
        }
        ```
    - response: `Same as /devices/{external_id} GET response`

  - /{external_id}/properties *DELETE*
    - purpose: Delete device's properties
    - request:
        ```
        {
          "properties": [
            {"key": "k", "value": "v"},  # Request str type (quoted) value means key k's type is "string"
            {"key": "k", "value": 1}  # Request int type (not-quoted) value means key k's type is "int"
          ]
        }
        ```
    - response: `Same as /devices/{external_id} GET response`

  - /{external_id}/notifications *GET*
    - purpose: Fetch device's tracked notifications with orders
    - query_string:
        ```
        events=...event id..., ... (comma-separated string)
        order_bys=...available field name..., ... (comma-separated string)
        size=...size for response array...
        start=...start...
        ```
    - request: `Empty`
    - response:
        ```
        {
          "success": ...,
          "result": {
            "total": ...total event amount...,
            "events": [
              {
                "id": ...sequential number...,
                "notification": {
                  ... notification ...
                },
                "event": ...event type..,
                "created_at": ...,
              },
              ...
            ]
          },
          "reason": ...,
        }
        ```
  - /-/:search *POST*
    - purpose: Get devices that is matched for conditions
    - request:
        ```{
            "external_ids": [
              {... device ids ... },
            ],
            "conditions": {
              "conditions": [ ... conditions ... ],
              "key": ...compare key...[str],
              "value": ...compare value...[str],
              "operator": ... operator e.g) str_eq/int_lte....[str],
              "join_type": ...[AND|OR]...[str]
             },
            "start": 0,
            "size": 10
        }
        ```
    - response:
        ```
        {
          "success": ...,
          "result": [
              {
                    "id": ..sequential number..,
                    "external_id": ...device id...,
                    "push_token": ...,
                    "send_platform": ...,
                    "device_platform": ...,
                    "created_at": ...,
                    "modified_at": ...,
                    "device_properties": [ {...key...: ...value...}, ... ]
                  }
              ]
          "reason": ...,
        }
        ```

### Notification management

- /notifications
  - /{notification_id} *GET*
    - purpose: Fetch selected notification information
    - request: `Empty`
    - response:
        ```
        {
          "success": ...,
          "result": {
              "id": ...sequential number...,
              "uuid": ...notification id...,
              "title": ...,
              "body": ...,
              "sent": ...sent count (result)...,
              "deep_link": ...landing link...,
              "image_url": ...,
              "icon_url": ...,
              "conditions": {
                 "conditions": [ ... conditions ... ],
                 "key": ...compare key...[str],
                 "value": ...compare value...[str],
                 "operator": ... operator e.g) str_eq/int_lte....[str],
                 "join_type": ...[AND|OR]...[str]
              },
              "status": ...,
              "scheduled_at": ...push scheduled time...,
              "created_at": ...,
              "modified_at": ...,
          },
          "reason": ...,
        }
        ```

  - / *GET*
    - purpose: Fetch ordered notifications information
    - query_string:
        ```
        order_bys=...available field name..., ... (comma-separated string)
        size=...size for response array...
        start=...start...
        ```
    - request: `Empty`
    - response:
        ```
        {
          "success": ...,
          "result": [
            {
              "id": ...sequential number...,
              "uuid": ...notification id...,
              "title": ...,
              "body": ...,
              "sent": ...sent count (result)...,
              "deep_link": ...landing link...,
              "image_url": ...,
              "icon_url": ...,
              "conditions": {
                 "conditions": [ ... conditions ... ],
                 "key": ...compare key...[str],
                 "value": ...compare value...[str],
                 "operator": ... operator e.g) str_eq/int_lte....[str],
                 "join_type": ...[AND|OR]...[str]
              },
              "status": ...,
              "scheduled_at": ...push scheduled time...,
              "created_at": ...,
              "modified_at": ...,
            },
            ...
          ]
          "reason": ...,
        }
        ```

  - /{notification_id}/:launch *POST*
    - purpose: Launch push campaign
    - request: `Empty`
    - response: `Same as /notifications/{notification_id} GET response`

  - /-/launched *GET*
    - purpose: Fetch launched notifications
    - query_string:
        ```
        size=...size for response array...
        start=...start...
        ```
    - request: `Empty`
    - response: `Same as / GET response`


### Internal API

- /internal
  - /devices/logs/notification:add *POST*
    - purpose: Create device's notification log (notification worker uses)
    - request:
        ```
        {
          "device_ids": [, ...int], # Device's PK value (device.id) not external id
          "notification_id": ..int, # Notification's PK value (notification.id) not notification uuid
        }
        ```
    - response:
        ```
        {
          "success": ...,
          "result": ...int, # Requested device count (if bulk insertion completely done)
          "reason": ...,
        }
        ```

  - /notifications/{notification_uuid}/sent:increase *POST*
    - purpose: Increase notification's sent amount by device_platform (result worker uses)
    - request:
        ```
        {
          "ios": ...int, # Increase amount for ios sent
          "android": ...int, # Increase amount for android sent
        }
        ```
    - response:
        ```
        {
          "success": ...,
          "result": {
              "ios": ...int, # Increased value for ios sent
              "android": ...int, # Increased value for android sent
          }
          "reason": ...,
        }
        ```
