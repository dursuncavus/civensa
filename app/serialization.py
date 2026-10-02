import json
from decimal import Decimal


def json_dumps(value, **kwargs):
    def encode(item):
        if isinstance(item, Decimal):
            return format(item, 'f')
        raise TypeError(f'Unsupported type: {type(item).__name__}')
    return json.dumps(value, default=encode, **kwargs)
