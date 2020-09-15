"""
:Author: PDT
:Since: 2020/05/28

The package contains everything ``Asset`` related.
"""

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Any, MutableMapping, Optional
from uuid import uuid4


@dataclass
class Asset:
    """This is an ``Asset``."""

    data: MutableMapping[Any, Any]
    created: datetime = None
    updated: datetime = None
    asset_id: Optional[int] = None
    extended_by_id: Optional[int] = 0

    def __hash__(self):
        return hash(uuid4())

    def __eq__(self, other):
        if not isinstance(other, Asset):
            return False
        if self.as_dict() == other.as_dict():
            return True
        return False

    def as_dict(self):
        """Get a dict from an Asset."""

        data = {}
        for key, value in self.data.items():
            if isinstance(value, datetime):
                data[key] = int(value.timestamp())
                continue
            if isinstance(value, date):
                data[key] = int(datetime.combine(value, time(0)).timestamp())
                continue
            if isinstance(value, type(None)):
                data[key] = 'null'
                continue
            data[key] = value

        return {
            'data': data,
            'asset_id': self.asset_id,
            'created': int(self.created.timestamp()),
            'updated': int(self.updated.timestamp()),
            'extended_by_id': self.extended_by_id
        }
