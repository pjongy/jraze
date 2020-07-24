import datetime
import random
import string

from dateutil.parser import parse

from common.exception.parser import DatetimeParsingError

KST = datetime.timezone(datetime.timedelta(hours=9), 'KST')
UTC = datetime.timezone(datetime.timedelta(hours=0), 'UTC')


def json_encoder(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()


def to_string(string):
    if isinstance(string, bytes):
        return string.decode()

    if isinstance(string, int):
        return str(string)

    if isinstance(string, str):
        return string

    raise TypeError(
        f'Passed value is not str or bytes or int ({type(string)})')


def string_to_utc_datetime(datestring):
    if datestring:
        try:
            datetime_ = parse(datestring)
        except ValueError as e:
            raise DatetimeParsingError(e)

        if not datetime_.tzinfo:
            return datetime_.replace(tzinfo=UTC)
        else:
            return datetime_.astimezone(UTC)


def datetime_to_utc_datetime(datetime_):
    if datetime_:
        if not datetime_.tzinfo:
            return datetime_.replace(tzinfo=UTC)
        else:
            return datetime_.astimezone(UTC)


def datetime_to_kst_datetime(datetime_):
    if datetime_:
        if not datetime_.tzinfo:
            return datetime_.replace(tzinfo=KST)
        else:
            return datetime_.astimezone(KST)


def utc_now():
    current_time = datetime.datetime.now(UTC)
    return current_time


def kst_now():
    current_time = datetime.datetime.now(KST)
    return current_time


def random_string(length=8):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for i in range(length))
