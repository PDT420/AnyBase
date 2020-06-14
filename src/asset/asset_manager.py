"""
:Author: PDT
:Since: 2020/05/28

This is the the module for the resource manager.
"""

from asset.asset_type_manager import AssetTypeManager
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

    def update_asset(self, asset: Asset):
        """Update the information on an asset in the database."""

    def get_all(self, asset_type: AssetType):
        """Get all assets of ``AssetType`` from the database."""
