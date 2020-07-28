import enum

import typing
from tortoise import fields
from tortoise.models import Model

from common.model.mixin import TimestampMixin


class NotificationStatus(enum.IntEnum):
    CREATED = 0
    SENT = 1
    ERROR = 2
    DELETED = 2


class Notification(Model, TimestampMixin):
    class Meta:
        table = 'notification'

    id = fields.UUIDField(pk=True)
    title = fields.CharField(max_length=255)
    body = fields.TextField()
    image_url = fields.TextField(null=True)
    icon_url = fields.TextField(null=True)
    deep_link = fields.TextField(null=True)
    sent = fields.IntField(default=0)
    scheduled_at = fields.DatetimeField(null=True)
    conditions = fields.JSONField(default={})
    status = typing.cast(
        NotificationStatus,
        fields.IntEnumField(NotificationStatus)
    )
