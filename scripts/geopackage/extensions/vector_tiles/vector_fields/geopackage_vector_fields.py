#!/usr/bin/python2.7
"""
Copyright (C) 2014 Reinventing Geospatial, Inc.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>,
or write to the Free Software Foundation, Inc., 59 Temple Place -
Suite 330, Boston, MA 02111-1307, USA.

Author: Jenifer Cochran, Reinventing Geospatial Inc (RGi)
Date: 2018-11-11
   Requires: sqlite3, argparse
   Optional: Python Imaging Library (PIL or Pillow)
Credits:
  MapProxy imaging functions: http://mapproxy.org
  gdal2mb on github: https://github.com/developmentseed/gdal2mb

Version:
"""

from scripts.geopackage.extensions.extension import Extension, EXTENSION_READ_WRITE_SCOPE
from scripts.geopackage.extensions.vector_tiles.vector_fields.vector_fields_entry import VectorFieldsEntry
from scripts.geopackage.extensions.vector_tiles.vector_layers.geopackage_vector_layers import \
    GEOPACKAGE_VECTOR_LAYERS_TABLE_NAME
from scripts.geopackage.extensions.vector_tiles.vector_tiles_constants import VECTOR_TILES_EXTENSION_NAME, \
    VECTOR_TILES_DEFINITION
from scripts.geopackage.utility.sql_utility import table_exists
from sqlite3 import Cursor

GEOPACKAGE_VECTOR_FIELDS_TABLE_NAME = "gpkgext_vt_fields"


class GeoPackageVectorFields(Extension):
    """
    Object representation of the gpkgext_vt_fields table. This table is one of the relational tables for the Vector
    Tiles Extension.
    """

    def __init__(self):
        super(GeoPackageVectorFields, self).__init__(table_name=GEOPACKAGE_VECTOR_FIELDS_TABLE_NAME,
                                                     column_name=None,
                                                     scope=EXTENSION_READ_WRITE_SCOPE,
                                                     extension_name=VECTOR_TILES_EXTENSION_NAME,
                                                     definition=VECTOR_TILES_DEFINITION)

    @staticmethod
    def create_vector_fields_table(cursor):
        """
        Creates the Vector Fields Table (gpkgext_vt_fields)

        :param cursor: the cursor to the GeoPackage database's connection
        :type cursor: Cursor
        """

        cursor.execute("""
                         CREATE TABLE IF NOT EXISTS {table_name}
                         (id         INTEGER PRIMARY KEY AUTOINCREMENT, -- primary key
                          layer_id   INTEGER             NOT NULL,      -- is a foreign key to id in gpkgext_vt_layers
                          name       TEXT                NOT NULL,      -- is the field name
                          type       TEXT                NOT NULL,      -- either String, Number, or Boolean
                          CONSTRAINT fk_vt_layer_id FOREIGN KEY (layer_id) REFERENCES {vector_layers_table_name}(id) 
                         );
                       """.format(table_name=GEOPACKAGE_VECTOR_FIELDS_TABLE_NAME,
                                  vector_layers_table_name=GEOPACKAGE_VECTOR_LAYERS_TABLE_NAME))

    @staticmethod
    def get_all_vector_fields_entries(cursor):
        """
        Returns all the entries as a a list of Vector Field Entry objects representing the rows in the GeoPackage Vector
        Fields Table

        :param cursor: the cursor to the GeoPackage database's connection
        :type cursor: Cursor

        :return: a list of Vector Field Entry objects representing the rows in the GeoPackage Vector Fields Table
        :rtype: list of VectorFieldsEntry
        """
        if not table_exists(cursor, GEOPACKAGE_VECTOR_FIELDS_TABLE_NAME):
            return []

        # select all the rows
        cursor.execute("SELECT * FROM {table_name};".format(table_name=GEOPACKAGE_VECTOR_FIELDS_TABLE_NAME))

        rows = cursor.fetchall()

        if rows is None:
            return []

        return [VectorFieldsEntry(layer_id=row['layer_id'],
                                  name=row['name'],
                                  field_type=row['type']) for row in rows]

    @staticmethod
    def get_vector_field_entry_by_values(cursor,
                                         id=None,
                                         layer_id=None,
                                         name=None,
                                         type=None):
        """
        Will search the gpkgext_vt_fields table for any entries with the values specified.  Any value that is specified
        as None will not be included in the search:

        If any value is None- wont check that value in the where clause since none of the values in this table
        are allowed to be None. Values that are not none will be included in the where clause to find any vector field
        with those specified values.

        :param cursor: the cursor to the GeoPackage database's connection
        :type cursor: Cursor

        :param id: primary key of the row in gpkgext_vt_fields
        :type id: int

        :param layer_id: is a foreign key to id in gpkgext_vt_layers
        :type layer_id: int

        :param name: the name of the field
        :type name: str

        :param type: the Vector Field type must be boolean, number, or string
        :type type: VectorFieldType

        :return: a list of Vector Field Entries that match the values given
        :rtype: list of VectorFieldEntry
        """
        if not table_exists(cursor, GEOPACKAGE_VECTOR_FIELDS_TABLE_NAME):
            return []

        columns_clauses = list()
        values_list = list()

        if id is not None:
            columns_clauses.append(" id = ? ")
            values_list.append(id)
        if layer_id is not None:
            columns_clauses.append(" layer_id = ? ")
            values_list.append(layer_id)
        if name is not None:
            columns_clauses.append(" name = ? ")
            values_list.append(name)
        if type is not None:
            columns_clauses.append(" type = ? ")
            values_list.append(type.value)

        if len(values_list) == 0:
            raise ValueError("Must specify at least one value to search for! Not all values can be None!")

        where_clause = ' AND '.join(columns_clauses)

        cursor.execute("SELECT * FROM {table_name} WHERE {where_clause};"
                       .format(table_name=GEOPACKAGE_VECTOR_FIELDS_TABLE_NAME,
                               where_clause=where_clause),
                       values_list)

        rows = cursor.fetchall()

        if rows is None:
            return []

        return [VectorFieldsEntry(layer_id=row['layer_id'],
                                  name=row['name'],
                                  field_type=row['type']) for row in rows]

    @staticmethod
    def insert_or_update_vector_tile_field_entry(cursor, vector_tiles_field_entry):
        """

        :param cursor: the cursor to the GeoPackage database's connection
        :type cursor: Cursor

        :param vector_tiles_field_entry:
        :type vector_tiles_field_entry: VectorFieldsEntry
        """
        if not table_exists(cursor, GEOPACKAGE_VECTOR_FIELDS_TABLE_NAME):
            raise ValueError("Cannot add to {table} because {table} does not exist. Be sure to create the default "
                             "vector-tiles tables before calling this method."
                             .format(table=GEOPACKAGE_VECTOR_FIELDS_TABLE_NAME))

        cursor.execute("""
                          INSERT OR REPLACE INTO {table_name} (layer_id,
                                                               name,
                                                               type)
                          VALUES (?, ?, ?);
                       """.format(table_name=GEOPACKAGE_VECTOR_FIELDS_TABLE_NAME),
                       (vector_tiles_field_entry.layer_id,
                        vector_tiles_field_entry.name,
                        vector_tiles_field_entry.type.value))
