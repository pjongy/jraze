from tortoise import fields
from tortoise.models import Model


class DeviceNotificationLog(Model):
    class Meta:
        table = 'device_notification_log'

    id = fields.IntField(pk=True)
    device = fields.ForeignKeyField('models.Device', related_name='device_notification_logs')
    notification = fields.ForeignKeyField(
        'models.Notification',
        related_name='device_notification_logs'
    )
    created_at = fields.DatetimeField(null=True, auto_now_add=True)
