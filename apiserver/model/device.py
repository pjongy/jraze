import enum
import typing

from tortoise import fields
from tortoise.models import Model

from apiserver.model.device_property import DeviceProperty
from apiserver.model.mixin import TimestampMixin


class DevicePlatform(enum.IntEnum):
    UNKNOWN = 0
    ANDROID = 1
    IOS = 2
    WEB = 3


class SendPlatform(enum.IntEnum):
    UNKNOWN = 0
    FCM = 1
    APNS = 2


class Device(Model, TimestampMixin):
    class Meta:
        table = 'device'

    id = fields.BigIntField(pk=True)
    external_id = fields.CharField(max_length=255, index=True)
    push_token = fields.CharField(max_length=255, index=True, null=True)  # push token from fcm
    send_platform = typing.cast(
        SendPlatform,
        fields.IntEnumField(DevicePlatform)
    )
    device_platform = typing.cast(
        DevicePlatform,
        fields.IntEnumField(DevicePlatform)
    )
    device_properties: fields.ReverseRelation[DeviceProperty]
