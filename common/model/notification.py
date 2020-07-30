import enum

import typing
from tortoise import fields
from tortoise.models import Model

from common.model.mixin import TimestampMixin


class NotificationStatus(enum.IntEnum):
    DRAFT = 0
    LAUNCHED = 1
    SENT = 2
    ERROR = 3
    DELETED = 4


class Notification(Model, TimestampMixin):
    class Meta:
        table = 'notification'

    id = fields.IntField(pk=True)
    uuid = fields.UUIDField(index=True)
    title = fields.CharField(max_length=255)
    body = fields.TextField()
    image_url = fields.TextField(null=True)
    icon_url = fields.TextField(null=True)
    deep_link = fields.TextField(null=True)
    sent = fields.IntField(default=0)
    scheduled_at = fields.DatetimeField()
    conditions = fields.JSONField(default={})
    status = typing.cast(
        NotificationStatus,
        fields.IntEnumField(NotificationStatus)
    )
