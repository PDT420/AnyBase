"""
:Author: PDT
:Since: 2020/06/02

This is the module for the ``AssetTypeManager``.
"""

from datetime import datetime
from typing import Any
from typing import List
from typing import Mapping
from typing import Optional
from typing import Sequence
from typing import Union
from warnings import warn

from asset_type import AssetType
from asset_type.abstract_asset_type_manager import AAssetTypeManager
from database import Column
from database import DataTypes
from database.db_connection import DbConnection
from database.sqlite_connection import SqliteConnection
from exceptions.asset import AssetTypeAlreadyExistsException
from exceptions.asset import AssetTypeChangedException
from exceptions.asset import AssetTypeDoesNotExistException
from exceptions.asset import AssetTypeInconsistencyException
from exceptions.common import InvalidArgumentError
from exceptions.common import KeyConstraintException


class AssetTypeManager(AAssetTypeManager):
    """This is the ``AssetTypeManager``."""

    # Required fields
    db_connection: DbConnection = None

    ASSET_TYPE_HEADERS: Sequence[str] = None
    _asset_types_table_name: str = None

    def __init__(self):
        """Create a new ``AssetTypeManager``."""

        self.ASSET_NAME = 'asset_name'
        self.PRIMARY_KEY = 'primary_key'
        self.CREATED = 'abintern_created'
        self.UPDATED = 'abintern_updated'

        self.ASSET_TYPE_HEADERS = [
            self.ASSET_NAME,  # The name of the asset e.g: DVD, Book, Yacht, ...
            'asset_columns',  # A string generated by method in abstract superclass
            'asset_table_name',  # Name of the database table - also generated in abstract super class
            'super_type',  # Id of the asset type this one is 'sub' to
            'is_slave',  # Flag indicating whether this is a slave type of not
            'owner_id',  # Id of this asset types owner
            'booking_type_id',  # Id of the booking type of this asset type
            self.CREATED,  # Datetime this asset type was created
            self.UPDATED,  # Datetime this asset type was last updated
            self.PRIMARY_KEY  # Db Primary key of this type. Pk is generated by the db and is used as uid of the type
        ]
        self._asset_types_table_name = 'abintern_asset_types'

        self.db_connection = SqliteConnection.get()

        # Ensuring the table, to store the asset types in, exists
        self._init_asset_types_table()

    def create_asset_type(self, asset_type: AssetType) -> AssetType:
        """Create a new ``asset_type_id`` in the asset type registry."""

        # Assuring one can't create more than one asset type with the same name
        if self.check_asset_type_exists(asset_type):
            raise AssetTypeAlreadyExistsException(
                f"The asset type {asset_type.asset_name} already exists!")

        # Now, is when this asset type was created
        created: datetime = datetime.now().replace(microsecond=0)

        # Checking if a booking type must be created.
        # Creating the booking type if required.
        booking_type: Optional[AssetType] = None
        if asset_type.bookable is True:
            booking_type = AssetType(
                asset_name=f'abbookings_{asset_type.asset_name}'.replace(' ', '_').lower(),
                columns=[
                    Column('From', 'from_time', DataTypes.DATETIME.value, required=True),
                    Column('Until', 'until_time', DataTypes.DATETIME.value, required=True),
                    Column('Booker Type Id', 'booker_type_id', DataTypes.INTEGER.value, required=True),
                    Column('Booker Id', 'booker_id', DataTypes.INTEGER.value, required=True),
                    Column('Booked Asset Id', 'booked_asset_id', DataTypes.INTEGER.value, required=True)
                ])  # NOTE: The booking_type is a private slave!
            booking_type = self.create_asset_type(booking_type)
            asset_type.booking_type_id = booking_type.asset_type_id

        # Creating a query dict (as required by write_dict),
        # from the asset type and handing it to the database.

        asset_table_name: str = AssetTypeManager.generate_asset_table_name(asset_type)

        query_dict: Mapping[str, Any] = {
            self.PRIMARY_KEY: asset_type.asset_type_id,
            self.ASSET_NAME: asset_type.asset_name,
            'asset_table_name': asset_table_name,
            self.CREATED: int(created.timestamp()),
            self.UPDATED: int(created.timestamp()),
            'asset_columns': self.generate_column_str_from_columns(asset_type.columns),
            'super_type': asset_type.get_super_type_id(),
            'is_slave': asset_type.is_slave,
            'owner_id': asset_type.owner_id,
            'booking_type_id': asset_type.booking_type_id,
        }

        # Storing the asset type in the database
        asset_type_id: int = self.db_connection.write_dict(
            self._asset_types_table_name, query_dict)

        # Updating the booking types owner_id
        # to the id of the asset_type we just
        # created. Master and Slave from Birth.
        # \(@^0^@)/    \(@^0^@)/    \(@^0^@)/
        if asset_type.bookable is True and isinstance(booking_type, AssetType):
            booking_type.owner_id = asset_type_id
            booking_type.is_slave = True
            self.update_asset_type(booking_type)

        # Adding obligatory columns to the asset_table
        asset_table_columns = asset_type.columns + [
            Column('Created', self.CREATED, DataTypes.DATETIME.value, required=True),
            Column('Updated', self.UPDATED, DataTypes.DATETIME.value, required=True),
            Column('Super Type', 'abintern_extended_by_id', DataTypes.INTEGER.value, required=True),
            Column('Sub Type', 'abintern_sub_type_id', DataTypes.INTEGER.value, required=True),
            Column('Sub Asset', 'abintern_sub_id', DataTypes.INTEGER.value, required=True)
        ]

        # Creating the asset table
        self.db_connection.create_table(asset_table_name, asset_table_columns)
        self.db_connection.commit()

        return AssetType(
            asset_name=asset_type.asset_name,
            columns=asset_type.columns,
            created=created,
            updated=created,
            asset_table_name=asset_table_name,
            asset_type_id=asset_type_id,
            super_type=asset_type.super_type,
            is_slave=asset_type.is_slave,
            owner_id=asset_type.owner_id,
            bookable=asset_type.bookable,
            booking_type_id=asset_type.booking_type_id)

    def delete_asset_type(self, asset_type: AssetType) -> None:
        """Delete ``asset_type_id`` and all it's assets from the system."""

        self.db_connection.delete(self._asset_types_table_name, [f"primary_key = {asset_type.asset_type_id}"])
        self.db_connection.delete_table(self.generate_asset_table_name(asset_type))
        self.db_connection.commit()

    def update_asset_type(self, asset_type: AssetType, extend_columns: bool = True) -> AssetType:
        """Update an ``asset_type_id`` in the database."""

        # Making sure one is not trying to
        # update an asset type without an id.
        if not asset_type.asset_type_id:
            raise AttributeError(
                "The asset_type_id parameter of an AssetType " +
                "you are trying to update must exist!"
            )

        # Getting the old asset type from the database.
        db_asset_type = self.get_one_by_id(asset_type.asset_type_id)

        if not db_asset_type:
            raise AssetTypeDoesNotExistException(
                "The asset type you are trying to update does not exist!")

        # Check if the asset_type has been updated
        # by someone else in the meantime.
        if db_asset_type.updated > asset_type.updated:
            raise AssetTypeChangedException(
                "The AssetType you are trying to update, has been changed!")

        # Generating the updated table name
        updated_table_name = self.generate_asset_table_name(asset_type)

        # Updating the "abasset.." tables name
        if db_asset_type.asset_name != asset_type.asset_name:

            # Making sure one can't update to a name that already exists
            if self.check_asset_type_exists(asset_type):
                raise AssetTypeAlreadyExistsException(
                    "Can't perform update - AssetType with that name already exists!")

            self.db_connection.update_table_name(
                db_asset_type.asset_table_name,
                updated_table_name)

        # Updating the "abasset.." tables columns
        if len(db_asset_type.columns) != len(asset_type.columns):
            # TODO: implement remove, append columns
            raise NotImplementedError(
                "Removing, appending columns to asset " +
                "type is not yet implemented!")

        update_columns: Mapping[str, Column] = {
            col.db_name: asset_type.columns[index]
            for index, col in enumerate(db_asset_type.columns)
        }

        self.db_connection.update_columns(updated_table_name, update_columns)

        updated: datetime = datetime.now().replace(microsecond=0)

        # Creating a query dict as required by update
        query_dict: Mapping[str, Any] = {
            self.PRIMARY_KEY: asset_type.asset_type_id,
            self.ASSET_NAME: asset_type.asset_name,
            'asset_table_name': updated_table_name,
            self.CREATED: int(asset_type.created.timestamp()),
            self.UPDATED: int(updated.timestamp()),
            'asset_columns': self.generate_column_str_from_columns(asset_type.columns),
            'super_type': asset_type.super_type,
            'is_slave': asset_type.is_slave,
            'owner_id': asset_type.owner_id,
            'booking_type_id': asset_type.booking_type_id
        }
        self.db_connection.update(self._asset_types_table_name, query_dict)

        return self.get_one_by_id(asset_type.asset_type_id, extend_columns=extend_columns)

    def check_asset_type_exists(self, asset_type: Union[str, AssetType]) -> bool:
        """Check if ``asset_type_id`` with that name already exists."""

        if isinstance(asset_type, str):
            or_filters = [f"asset_name = '{asset_type}'"]

        elif isinstance(asset_type, AssetType):
            or_filters = [f"asset_name = '{asset_type.asset_name}'"]
            if asset_type.asset_type_id:
                or_filters = [f"primary_key = {asset_type.asset_type_id}"]
        else:
            raise InvalidArgumentError(
                "The asset_type_id parameter of the AssetTypeManager " +
                "must be filled with either an asset_name str or " +
                "an AssetType!")

        db_response = self.db_connection.read(
            table_name=self._asset_types_table_name,
            headers=[self.PRIMARY_KEY, self.ASSET_NAME],
            or_filters=or_filters)

        if not bool(db_response):
            return False

        table_exists = self.db_connection.check_table_exists(
            AssetTypeManager.generate_asset_table_name(asset_type))
        return table_exists

    def get_one_by_id(self, asset_type_id: int, extend_columns: bool = False) -> Optional[AssetType]:
        """Get the ``AssetType`` with ident ``asset_type_id``."""

        # Reading asset types from the database
        result: Sequence[Mapping[str, Any]] = self.db_connection.read(
            table_name=self._asset_types_table_name,
            headers=self.ASSET_TYPE_HEADERS,
            and_filters=[f'{self.PRIMARY_KEY} = {asset_type_id}']
        )

        if len(result) > 1:
            raise KeyConstraintException(
                "There is a real big problem here! Real biggy - trust me." +
                "The primary key constraint is broken!"
            )

        return self._get_one(result, extend_columns)

    def get_one_by_name(self, asset_type_name: str, extend_columns: bool = False) -> Optional[AssetType]:
        """Get the ``AssetType`` called ``asset_type_name``."""

        # Reading asset types from the database
        result: Sequence[Mapping[str, Any]] = self.db_connection.read(
            table_name=self._asset_types_table_name,
            headers=self.ASSET_TYPE_HEADERS,
            and_filters=[f"asset_name = '{asset_type_name}'"])

        if len(result) > 1:
            raise KeyConstraintException(
                "There is a real big problem here! Real biggy - trust me." +
                "The asset_name unique constraint is broken!")

        return self._get_one(result, extend_columns)

    def _get_one(self, result: Sequence[Mapping], extend_columns: bool = False) -> Optional[AssetType]:
        """Get the ``AssetType`` with ident ``asset_type_id``."""

        if len(result) < 1:
            return None

        # TODO: Think about marking columns as extended columns
        # TODO: So the asset type server does not have to load

        asset_type: AssetType = self._convert_result_to_asset_type(result[0])

        if (super_type_id := int(result[0]['super_type'])) > 0 and extend_columns:
            super_type: AssetType = self.get_one_by_id(super_type_id, extend_columns=True)
            asset_type.columns.extend(super_type.columns)

        return asset_type

    def get_all(self, ignore_slaves: bool = True) -> List[AssetType]:
        """Get all ``AssetTypes`` registered in the database."""

        # Ensuring the table to get asset types from exists
        self._init_asset_types_table()

        # TODO: Generalize filters, so they can be used to
        # TODO: address any implementation of DbConnection.

        filters: List[str] = []

        if ignore_slaves is True:
            # This will ignore all kinds of slaves
            filters.append('owner_id <= 0')
            filters.append('is_slave = 0')

        # Reading asset types from the database
        results: Sequence[Mapping[str, Any]] = self.db_connection.read(
            table_name=self._asset_types_table_name,
            headers=self.ASSET_TYPE_HEADERS,
            and_filters=filters
        )

        return self._convert_results_to_asset_types(results)

    def get_all_filtered(
            self, and_filters: List[str] = None,
            or_filters: Sequence[str] = None,
            ignore_slaves: bool = True
    ) -> List[AssetType]:
        """Get all ``AssetTypes`` for which the given filters apply."""

        if not and_filters and not or_filters:
            warn("Call to 'get_all_filtered()' without any filters. Use 'get_all()'!")
            return self.get_all()

        # TODO: Generalize filters, so they can be used to
        # TODO: address any implementation of DbConnection.

        and_filters = and_filters if and_filters else []
        or_filters = or_filters if or_filters else []

        if ignore_slaves is True:
            and_filters.append('owner_id <= 0')
            and_filters.append('is_slave = 0')

        # Ensuring the table to get asset types from exists
        self._init_asset_types_table()

        # Reading asset types from the database
        result: Sequence[Mapping[str, Any]] = self.db_connection.read(
            table_name=self._asset_types_table_name,
            headers=self.ASSET_TYPE_HEADERS,
            and_filters=and_filters,
            or_filters=or_filters
        )

        return self._convert_results_to_asset_types(result)

    def get_batch(
            self, offset: int, limit: int,
            and_filters: List[str] = None,
            or_filters: Sequence[str] = None,
            ignore_slaves: bool = True
    ) -> List[AssetType]:
        """Get a batch of ``AssetTypes`` from offset until limit."""

        # Ensuring the table to get asset types from exists
        self._init_asset_types_table()

        # TODO: Generalize filters, so they can be used to
        # TODO: address any implementation of DbConnection.

        and_filters = and_filters if and_filters else []
        or_filters = or_filters if or_filters else []

        if ignore_slaves is True:
            and_filters.append('is_slave = 0')
            and_filters.append('owner_id <= 0')

        # Reading asset types from the database
        result: Sequence[Mapping[str, Any]] = self.db_connection.read(
            table_name=self._asset_types_table_name,
            headers=self.ASSET_TYPE_HEADERS,
            and_filters=and_filters,
            or_filters=or_filters,
            limit=limit,
            offset=offset
        )

        return self._convert_results_to_asset_types(result)

    def get_type_children(self, asset_type: AssetType, depth: int = 0, ignore_slaves: bool = True):
        """Get the children tree of an asset_type."""

        children: List[AssetType] = self.get_all_filtered(
            and_filters=[f'"super_type" = {asset_type.asset_type_id}'],
            ignore_slaves=ignore_slaves)

        # Getting all the types we need to consider.
        # The depth parameter sets the depth we traverse
        # in the AssetType tree.
        _type_children: List[AssetType] = children
        while depth > 0 and _type_children:
            next_gen_children: List[AssetType] = []

            for child_type in _type_children:
                next_gen_children.extend(
                    self.get_type_children(child_type, ignore_slaves=False))

            children.extend(next_gen_children)
            _type_children = next_gen_children

        return children

    def get_slaves(self, asset_type: AssetType, pub_slaves: bool = True) -> List[AssetType]:
        """Get the slaves of this ``asset_type``."""

        # TODO: Generalize filters, so they can be used to
        # TODO: address any implementation of DbConnection.

        owner_filter: str = f'owner_id = {asset_type.asset_type_id}'
        is_slave_filter: str = 'is_slave = 1'

        or_filters = [f'({owner_filter} AND {is_slave_filter})']

        if pub_slaves is True:
            public_filter: str = 'owner_id = 0'
            or_filters = [f'({public_filter} AND {is_slave_filter})']

        slaves: List[AssetType] = self.get_all_filtered(
            or_filters=or_filters,
            ignore_slaves=False)

        return slaves

    def count(self, ignore_child_types: bool = False, ignore_slaves: bool = False):
        """Get the number of ``AssetTypes`` stored in the database."""

        and_filters: List[str] = []

        if ignore_child_types:
            and_filters.append('super_type = 0')

            if ignore_slaves:
                owner_filter: str = 'owner_id = 0'
                is_slave_filter: str = 'is_slave = 0'
                and_filters.append(f'({owner_filter} AND {is_slave_filter})')

        elif ignore_slaves:
            owner_filter: str = 'owner_id = 0'
            is_slave_filter: str = 'is_slave = 0'
            and_filters.append(f'({owner_filter} AND {is_slave_filter})')

        return self.db_connection.count(
            self._asset_types_table_name,
            and_filters=and_filters)

    def _convert_result_to_asset_type(self, result: Mapping) -> AssetType:
        """Convert one result row to an asset type."""

        return AssetType(
            asset_name=result[self.ASSET_NAME],
            columns=AssetTypeManager.generate_columns_from_columns_str(result['asset_columns']),
            created=datetime.fromtimestamp(result[self.CREATED]),
            updated=datetime.fromtimestamp(result[self.UPDATED]),
            asset_table_name=result.get('asset_table_name', None),
            asset_type_id=result[self.PRIMARY_KEY],
            super_type=result['super_type'],
            is_slave=result['is_slave'],
            owner_id=result['owner_id'],
            bookable=result['booking_type_id'] > 0,
            booking_type_id=result['booking_type_id']
        )

    def _convert_results_to_asset_types(self, results: Sequence[Mapping]) -> List[AssetType]:
        """Convert the db results to a list of AssetTypes."""

        assets_types: List[AssetType] = []
        for result in results:
            assets_types.append(self._convert_result_to_asset_type(result))
        return assets_types

    #####################
    #  PRIVATE METHODS  #
    #####################

    def _init_asset_types_table(self) -> None:
        """Initialize the required table ``abintern_asset_types``."""

        if not self.db_connection.check_table_exists(self._asset_types_table_name):
            columns = [
                # The column primary_key will be created automatically
                Column(self.ASSET_NAME, self.ASSET_NAME, DataTypes.VARCHAR.value, required=True, unique=True),
                Column('asset_columns', 'asset_columns', DataTypes.VARCHAR.value, required=True),
                Column('asset_table_name', 'asset_table_name', DataTypes.VARCHAR.value, required=True, unique=True),
                Column('created', self.CREATED, DataTypes.DATETIME.value, required=True),
                Column('updated', self.UPDATED, DataTypes.DATETIME.value, required=True),
                Column('super_type', 'super_type', DataTypes.INTEGER.value, required=True),
                Column('is_slave', 'is_slave', DataTypes.BOOLEAN.value, required=True),
                Column('owner_id', 'owner_id', DataTypes.INTEGER.value, required=True),
                Column('booking_type_id', 'booking_type_id', DataTypes.INTEGER.value, required=True)
            ]
            self.db_connection.create_table(self._asset_types_table_name, columns)

    def _check_asset_type_consistency(self) -> None:
        """Check if a database table exists for all the AssetTypes
        stored in ``abintern_asset_types``."""

        asset_types: Sequence[AssetType] = self.get_all()

        if not all([self.check_asset_type_exists(asset_type) for asset_type in asset_types]):
            raise AssetTypeInconsistencyException()
