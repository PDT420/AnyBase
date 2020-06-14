"""
:Author: PDT
:Since: 2020/05/28

This is the the module for the resource manager.
"""
from typing import Any, MutableMapping, Sequence

from asset.asset_type_manager import AssetTypeManager
from database import Column
from database.db_connection import DbConnection
from database.sqlite_connection import SqliteConnection
from asset import Asset, AssetType


class AssetManager:
    """This is the ``AssetManager``."""

    def __init__(self):
        """Create a new ``AssetManager``."""

        self.db_connection: DbConnection = SqliteConnection.get()
        self.asset_type_manager: AssetTypeManager = AssetTypeManager()

    def create_asset(self, asset: Asset):
        """Create an asset in the database."""

        if not self.asset_type_manager.check_asset_type_exists(asset.asset_type):
            return 0

        asset.data.update({'primary_key': None})

        self.db_connection.write_dict(asset.asset_type.asset_table_name, asset.data)
        self.db_connection.commit()

    def delete_asset(self, asset: Asset):
        """Delete an asset from the system."""
        # TODO
        pass

    def update_asset(self, asset: Asset):
        """Update the information on an asset in the database."""
        # TODO
        pass

    def get_all(self, asset_type: AssetType) -> Sequence[Asset]:
        """Get all assets of ``AssetType`` from the database."""

        if not self.asset_type_manager.check_asset_type_exists(asset_type):
            return []

        result: Sequence[MutableMapping[str, Any]] = self.db_connection.read(
            self, self.asset_type_manager.generate_asset_table_name(asset_type.asset_name),
            [column.name for column in asset_type.columns])

        assets = []
        for asset_row in result:
            assets.append(Asset(
                asset_id=asset_row.pop('primary_key'),
                asset_type=asset_type,
                data=self._convert_row_to_data(asset_row, asset_type.columns)
            ))

        return assets

    ###################
    # private methods #
    ###################

    def _convert_row_to_data(
            self, row: MutableMapping[str, Any],
            columns: Sequence[Column]) \
            -> MutableMapping[str, Any]:
        """Convert a row to a valid data entry of an ``Asset``."""

        data: MutableMapping[str, Any] = {column.name: row[column.name] for column in columns}

        return data