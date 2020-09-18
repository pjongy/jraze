from tortoise import fields
from tortoise.models import Model

from apiserver.model.mixin import TimestampMixin


class Device(Model, TimestampMixin):
    class Meta:
        table = 'device'

    id = fields.BigIntField(pk=True)
    external_id = fields.CharField(max_length=255, index=True, unique=True)
