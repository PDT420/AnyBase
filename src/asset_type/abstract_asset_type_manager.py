"""
:Author: PDT
:Since: 2020/07/26

This is the abstract implementation of an asset type manager. It is
to be thought of as a template for what an asset type manager should
look like. It also sets some standards of what such a manager must
be capable of for it to be operated by the system and what certain
infrastructural parts should be formed like, in order to maintain
interoperability.
"""

import json
from abc import abstractmethod
from typing import List
from typing import Optional
from typing import Sequence
from typing import Union

from asset_type import AssetType
from database import Column
from database import DataType
from exceptions.common import InvalidArgumentError


class AAssetTypeManager:
    """This is the abstract class for AssetTypeManagers."""

    @abstractmethod
    def create_asset_type(self, asset_type: AssetType) -> AssetType:
        """Create a new ``asset_type_id`` in the asset type registry."""
        pass

    @abstractmethod
    def delete_asset_type(self, asset_type: AssetType) -> None:
        """Delete ``asset_type_id`` and all it's assets from the system."""
        pass

    @abstractmethod
    def update_asset_type(self, asset_type: AssetType, extend_columns: bool = True) -> AssetType:
        """Update an ``asset_type_id`` in the database."""
        pass

    @abstractmethod
    def check_asset_type_exists(self, asset_type: Union[str, AssetType]) -> bool:
        """Check if ``asset_type_id`` with that id already exists."""
        pass

    @abstractmethod
    def get_all(self, ignore_slaves: bool = True) -> List[AssetType]:
        """Get all ``AssetTypes`` registered in the database."""
        pass

    @abstractmethod
    def get_all_filtered(
            self, and_filters: Sequence[str] = None,
            or_filters: Sequence[str] = None,
            ignore_slaves: bool = True
    ) -> List[AssetType]:
        """Get all ``AssetTypes`` for which the given filters apply."""
        pass

    @abstractmethod
    def get_batch(
            self, offset: int,
            limit: int,
            and_filters: Sequence[str] = None,
            or_filters: Sequence[str] = None,
            ignore_slaves: bool = True
    ) -> List[AssetType]:
        """Get a batch of ``AssetTypes`` from offset until limit."""
        pass

    @abstractmethod
    def get_one_by_id(self, asset_type_id: int, extend_columns: bool = False) -> Optional[AssetType]:
        """Get the ``AssetType`` with ident ``asset_type_id``."""
        pass

    @abstractmethod
    def get_one_by_name(self, asset_type_name: str, extend_columns: bool = False) -> Optional[AssetType]:
        """Get the ``AssetType`` called ``asset_type_name``."""
        pass

    @abstractmethod
    def get_type_children(self, asset_type: AssetType, depth: int = 0, ignore_slaves: bool = False) -> List[AssetType]:
        """Get the children tree of an asset_type."""
        pass

    @abstractmethod
    def get_slaves(self, asset_type: AssetType, pub_slaves: bool = True) -> List[AssetType]:
        """Get the slaves of this ``asset_type_id``."""
        pass

    @abstractmethod
    def count(self, ignore_child_types: bool = False, ignore_slaves: bool = False):
        """Get the number of ``AssetTypes`` stored in the database."""
        pass

    @staticmethod
    def generate_column_str_from_columns(columns: Sequence[Column]) -> str:
        """Generate a column str from a list of Columns. This method
        is part of the abstract asset type manager, to ensure
        interoperability of different implementations of asset type
        managers. The way an asset type store the columns of an asset
        is a basic concept of the software and should be the same
        everywhere."""

        column_data = [json.dumps(column.as_dict()) for column in columns]
        column_str: str = ';'.join([col_data.replace('"', "'") for col_data in column_data])

        return column_str

    @staticmethod
    def generate_columns_from_columns_str(column_str: str) -> List[Column]:
        """Create a ``AssetType`` object from parameters. This function
        is part of the abstract asset type manager for the same reasons
        as for generate_str_column_from_columns. This it's counterpart.
        """

        columns: List[Column] = []

        for column_str in column_str.split(';'):
            column_data = json.loads(column_str.replace("'", '"'))
            column_data['datatype'] = DataType(**column_data['datatype'])
            columns.append(Column(**column_data))
        return columns

    @staticmethod
    def generate_asset_table_name(asset_type: Union[AssetType, str]) -> str:
        """Generate an ``asset_table_name`` from the ``asset type``.
        This method is part of the abstract asset type manager, to
        ensure, that future implementations still support the same
        naming convention."""

        if isinstance(asset_type, AssetType):
            asset_type_name = asset_type.asset_name.replace(' ', '_').lower()
        elif isinstance(asset_type, str):
            asset_type_name = asset_type.replace(' ', '_').lower()
        else:
            raise InvalidArgumentError()

        asset_table_name = f"abasset_table_{asset_type_name}"
        return asset_table_name
