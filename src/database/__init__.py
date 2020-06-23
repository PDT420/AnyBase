"""
:Author: PDT
:Since: 2020/05/27

This is the database package.
"""

from enum import Enum
from typing import NamedTuple


class DataType(NamedTuple):
    """This is a possible datatype."""
    typename: str
    db_type: str
    convert: callable


class DataTypes:
    """The available data types."""

    TEXT = DataType(typename='TEXT', db_type='VARCHAR', convert=str)
    VARCHAR = DataType(typename='TEXT', db_type='VARCHAR', convert=str)
    NUMBER = DataType(typename='NUMBER', db_type='REAL', convert=float)
    REAL = DataType(typename='NUMBER', db_type='REAL', convert=float)
    # TODO: Add additional required types
    # TODO: Update sqlite connection using this


class Column(NamedTuple):
    """This is a column, as required to create database column."""
    name: str
    datatype: DataType
    required: bool
