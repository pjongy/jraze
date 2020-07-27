from tortoise import fields
from tortoise.models import Model


class DeviceProperty(Model):
    class Meta:
        table = 'device_property'

    id = fields.BigIntField(pk=True)
    device = fields.ForeignKeyField('models.Device', related_name='device_properties')
    key = fields.CharField(max_length=255, index=True)
    value = fields.CharField(max_length=255, index=True)
