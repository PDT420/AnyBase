"""
:Author: PDT
:Since: 2020/05/28

The package contains the AssetManager and the AssetTypeManager.
"""
from dataclasses import dataclass
from datetime import date, datetime, time
from enum import Enum
from typing import Any, List, MutableMapping, Optional
from uuid import uuid4

from database import Column, DataTypes


@dataclass
class AssetType:
    """This is a ``AssetType``, it defines an asset."""

    asset_name: str
    columns: List[Column]
    created: datetime = None
    asset_table_name: str = None
    asset_type_id: int = None
    is_subtype: bool = False
    super_type_id: int = 0

    def as_dict(self):
        return {
            'asset_name': self.asset_name,
            'columns': [col.as_dict() for col in self.columns],
            'created': self.created,
            'asset_table_name': self.asset_table_name,
            'asset_type_id': self.asset_type_id,
            'is_subtype': self.is_subtype,
            'super_type_id': self.super_type_id
        }


@dataclass
class AssetTypePrefab:
    """This is an ``AssetTypePrefab``."""

    prefab_name: str
    columns: List[Column]

    def as_dict(self):
        return {
            'prefab_name': self.prefab_name,
            'columns': [col.as_dict() for col in self.columns],
        }


@dataclass
class AssetTypePrefabs(Enum):
    """These are the available ``AssetTypePrefabs``."""

    ADDRESS = AssetTypePrefab(
        prefab_name="Address",
        columns=[
            Column("Country", "country", DataTypes.TEXT.value, required=True),
            Column("City", "city", DataTypes.TEXT.value, required=True),
            Column("Street", "street", DataTypes.TEXT.value, required=True),
            Column("ZipCode", "zipcode", DataTypes.INTEGER.value, required=True),
            Column("House Number", "house_number", DataTypes.INTEGER.value, required=True),
        ],
    )

    # --

    @classmethod
    def get_all_asset_type_prefabs(cls):
        """Get all distinct field values from enum."""
        return list(set([prefab.value for prefab in cls.__members__.values()]))

    @classmethod
    def get_all_asset_type_prefab_names(cls):
        """Get the names of all available asset type prefabs."""
        return list(cls.__members__.keys())


@dataclass
class Asset:
    """This is an ``Asset``."""

    data: MutableMapping[Any, Any]
    created: datetime = None
    asset_id: Optional[int] = None

    def __hash__(self):
        return hash(uuid4())

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
            data[key] = value

        return {
            'data': data,
            'asset_id': self.asset_id,
            'created': self.created
        }
