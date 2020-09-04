import enum


class SendPlatform(enum.IntEnum):
    UNKNOWN = 0
    FCM = 1
    APNS = 2


class DevicePlatform(enum.IntEnum):
    UNKNOWN = 0
    Android = 1
    IOS = 2
