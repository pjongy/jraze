import datetime
import json
import uuid

from common.util import datetime_to_kst_datetime, datetime_to_utc_datetime


class ManualJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            r = datetime_to_kst_datetime(datetime_to_utc_datetime(o)).isoformat()
            return r
        if isinstance(o, uuid.UUID):
            return str(o)
        return super().default(o)
