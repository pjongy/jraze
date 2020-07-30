import enum

import typing
from tortoise import fields
from tortoise.models import Model


class Event(enum.IntEnum):
    NONE = 0
    SENT = 1
    RECEIVED = 2


class DeviceNotificationEvent(Model):
    class Meta:
        table = 'device_notification_event'

    id = fields.IntField(pk=True)
    device = fields.ForeignKeyField('models.Device', related_name='device_notification_events')
    notification = fields.ForeignKeyField(
        'models.Notification',
        related_name='device_notification_events'
    )
    event = typing.cast(
        Event,
        fields.IntEnumField(Event)
    )
    created_at = fields.DatetimeField(null=True, auto_now_add=True)
