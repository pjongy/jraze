import enum
import typing

from tortoise import fields
from tortoise.models import Model

from common.model.mixin import TimestampMixin


class DevicePlatform(enum.IntEnum):
    ANDROID = 0
    IOS = 1
    WEB = 2


class Device(Model, TimestampMixin):
    class Meta:
        table = 'device'

    id = fields.BigIntField(pk=True)
    device_id = fields.UUIDField(index=True)
    registration_id = fields.CharField(max_length=255, index=True)  # push token from fcm
    platform = typing.cast(
        DevicePlatform,
        fields.IntEnumField(DevicePlatform)
    )
