"""
:Author: PDT
:Since: 2020/06/02

This is the module for the AssetTypeManager.
"""
from typing import Any, Mapping, Optional, Sequence

from database import Column, DataTypes
from database.db_connection import DbConnection
from database.sqlite_connection import SqliteConnection
from asset import AssetType


class AssetTypeManager:
    """This is the ``AssetTypeManager``."""

    def __init__(self):
        """Create a new ``AssetTypeManager``."""

        self._asset_headers = ['asset_name', 'asset_columns', 'asset_table_name', 'primary_key']
        self._asset_types_table_name = 'abintern_asset_types'

        self.db_connection: DbConnection = SqliteConnection.get()

    def create_asset_type(self, asset_type: AssetType):
        """Create a new ``asset_type`` in the asset type registry."""

        # Ensuring the table to store the asset types in exists
        self._init_asset_types_table()

        if self.check_asset_type_exists(asset_type):
            self.db_connection.reset()

        # Creating a query dict as required by write_dict
        query_dict = {
            'primary_key': asset_type.asset_type_id,
            'asset_name': asset_type.asset_name,
            'asset_table_name': AssetTypeManager.generate_asset_table_name(asset_type),
            'asset_columns': ' '.join([
                f"{column.name} {column.datatype.db_type} {int(column.required)}"
                for column in asset_type.columns
            ])
        }

        # Storing the type information in the appropriate table
        self.db_connection.write_dict(self._asset_types_table_name, query_dict)

        # Creating a table appropriate for the asset_type
        self.db_connection.create_table(
            AssetTypeManager.generate_asset_table_name(asset_type),
            asset_type.columns
        )
        self.db_connection.commit()

    def delete_asset_type(self, asset_type: AssetType):
        """Delete ``asset_type`` and all it's assets from the system."""

        self.db_connection.delete(self._asset_types_table_name, [f"primary_key = {asset_type.asset_type_id}"])
        self.db_connection.delete_table(self.generate_asset_table_name(asset_type))
        self.db_connection.commit()

    def update_asset_type(self, asset_type: AssetType):
        """Update an ``asset_type`` in the database."""
        # TODO
        pass

    def check_asset_type_exists(self, asset_type: AssetType) -> bool:
        """Check if ``asset_type`` exists."""

        db_response = self.db_connection.read(
            table_name=self._asset_types_table_name,
            headers=['primary_key', 'asset_name'],
            or_filters=[
                f"asset_name = '{asset_type.asset_name}'"
            ]
        )

        table_exists = self.db_connection.check_table_exists(
            AssetTypeManager.generate_asset_table_name(asset_type))
        return bool(db_response) and table_exists

    def get_all(self) -> Sequence[AssetType]:
        """Get all ``AssetTypes`` registered in the database."""

        # Ensuring the table to store the asset types in exists
        self._init_asset_types_table()

        # Reading asset types from the database
        result: Sequence[Mapping[str, Any]] = self.db_connection.read(
            table_name=self._asset_types_table_name,
            headers=self._asset_headers
        )

        assets_types = []
        for asset_type_row in result:
            assets_types.append(self.get_asset_type_from_str(
                asset_name=asset_type_row['asset_name'],
                asset_columns=asset_type_row['asset_columns'],
                asset_table_name=asset_type_row['asset_table_name'],
                asset_type_id=asset_type_row['primary_key']
            ))

        return assets_types

    def get_one(self, asset_type_id: int) -> Optional[AssetType]:
        """Get the ``AssetType`` with id ``asset_type_id``."""

        # Ensuring the table to store the asset types in exists
        self._init_asset_types_table()

        # Reading asset types from the database
        result: Sequence[Mapping[str, Any]] = self.db_connection.read(
            table_name=self._asset_types_table_name,
            headers=self._asset_headers,
            and_filters=[f'primary_key = {asset_type_id}']
        )

        if len(result) < 1:
            return None

        asset_type = self.get_asset_type_from_str(
            asset_name=result[0]['asset_name'],
            asset_columns=result[0]['asset_columns'],
            asset_table_name=result[0]['asset_table_name'],
            asset_type_id=result[0]['primary_key']
        )

        return asset_type

    ######################
    #   STATIC METHODS   #
    ######################

    @staticmethod
    def get_asset_type_from_str(
            asset_type_id: int,
            asset_name: str,
            asset_table_name: str,
            asset_columns: str
    ):
        """Create a ``AssetType`` object from parameters."""

        asset_columns = asset_columns.split(' ')

        return AssetType(
            asset_type_id=asset_type_id,
            asset_name=asset_name,
            asset_table_name=asset_table_name,
            columns=[
                Column(name, DataTypes.__dict__[datatype], bool(int(required)))
                for name, datatype, required in [
                    asset_columns[i:i + 3] for i in range(0, len(asset_columns), 3)
                ]
            ]
        )

    @staticmethod
    def generate_asset_table_name(asset_type: AssetType) -> str:
        """Generate an ``asset_table_name`` from the ``asset type``."""
        return f"abasset_table_{asset_type.asset_name}"

    #####################
    #  PRIVATE METHODS  #
    #####################

    def _init_asset_types_table(self):
        """Initialize the required table ``abintern_asset_types``."""

        if not self.db_connection.check_table_exists(self._asset_types_table_name):
            columns = [
                Column('asset_name', 'VARCHAR', True),
                Column('asset_table_name', 'VARCHAR', True),
                Column('asset_columns', 'VARCHAR', True)
            ]
            self.db_connection.create_table(self._asset_types_table_name, columns)

    def _check_resource_type_consistency(self):
        """Check if a database table exists for all the AssetTypes
        stored in ``abintern_asset_types`` and vice versa."""
        # TODO: implement
        pass
