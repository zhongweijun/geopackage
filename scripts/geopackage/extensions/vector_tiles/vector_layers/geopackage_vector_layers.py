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
from scripts.geopackage.core.geopackage_core import GEOPACKAGE_CONTENTS_TABLE_NAME
from scripts.geopackage.extensions.extension import Extension, EXTENSION_READ_WRITE_SCOPE
from scripts.geopackage.extensions.vector_tiles.vector_layers.vector_layers_entry import VectorLayersEntry
from scripts.geopackage.extensions.vector_tiles.vector_tiles_constants import VECTOR_TILES_EXTENSION_NAME, \
    VECTOR_TILES_DEFINITION
from scripts.geopackage.utility.sql_utility import table_exists, select_query

GEOPACKAGE_VECTOR_LAYERS_TABLE_NAME = "gpkgext_vt_layers"


class GeoPackageVectorLayers(Extension):
    """
    Represents the GeoPackage Vector Layers table (gpkgext_vt_layers)
    """

    def __init__(self):
        super(GeoPackageVectorLayers, self).__init__(table_name=GEOPACKAGE_VECTOR_LAYERS_TABLE_NAME,
                                                     column_name=None,
                                                     scope=EXTENSION_READ_WRITE_SCOPE,
                                                     extension_name=VECTOR_TILES_EXTENSION_NAME,
                                                     definition=VECTOR_TILES_DEFINITION)

    @staticmethod
    def create_vector_layers_table(cursor):
        """
        Creates the Vector Tiles Layers Table (gpkgext_vt_layers)

        :param cursor: the cursor to the GeoPackage database's connection
        :type cursor: Cursor
        """

        cursor.execute("""
                         CREATE TABLE IF NOT EXISTS {table_name}
                         (id           INTEGER PRIMARY KEY AUTOINCREMENT, -- primary key
                          table_name   TEXT NOT NULL,                     -- table_name matches in the gpkg_contents
                          name         TEXT NOT NULL,                     -- name is layer name
                          description  TEXT,                              -- optional text description
                          minzoom      INTEGER,                           -- optional integer minimum zoom level
                          maxzoom      INTEGER,                           -- optional maximum zoom level
                          CONSTRAINT fk_gpkg_con_tbl_name FOREIGN KEY (table_name) REFERENCES {gpkg_contents}(table_name) 
                         );
                       """.format(table_name=GEOPACKAGE_VECTOR_LAYERS_TABLE_NAME,
                                  gpkg_contents=GEOPACKAGE_CONTENTS_TABLE_NAME))

    @staticmethod
    def get_all_vector_layers_entries(cursor):
        """
        Returns a list of Vector Layer entries that exist in the GeoPackage's gpkgext_vt_layers table
        :param cursor: the cursor to the GeoPackage database's connection
        :type cursor: Cursor

        :return a list of Vector Layer entries that exist in the GeoPackage's gpkgext_vt_layers table
        :rtype: list of VectorLayersEntry
        """
        if not table_exists(cursor, GEOPACKAGE_VECTOR_LAYERS_TABLE_NAME):
            return []

        # select all the rows
        cursor.execute("SELECT * FROM {table_name};".format(table_name=GEOPACKAGE_VECTOR_LAYERS_TABLE_NAME))

        return [VectorLayersEntry(table_name=row['table_name'],
                                  name=row['name'],
                                  description=row['description'],
                                  min_zoom=row['minzoom'],
                                  max_zoom=row['maxzoom'],
                                  id=row['id']) for row in cursor]

    @staticmethod
    def get_vector_layer_entries_by_table_name(cursor,
                                               vector_tiles_table_name):
        """
        Returns any Vector Layer Entries whose table_name column value matches the vector_tiles_table_name parameter.

        :param cursor: the cursor to the GeoPackage database's connection
        :type cursor: Cursor

        :param vector_tiles_table_name: the table_name of the vector tiles table that the entries in the vector
        layer table should match
        :type vector_tiles_table_name: str

        :return: Returns any Vector Layer Entries whose table_name column value matches the vector_tiles_table_name
        parameter.
        :rtype: list of VectorLayersEntry
        """
        if not table_exists(cursor, GEOPACKAGE_VECTOR_LAYERS_TABLE_NAME):
            return []

        # select all the rows
        cursor.execute("SELECT * FROM {table_name} WHERE table_name= ?;"
                       .format(table_name=GEOPACKAGE_VECTOR_LAYERS_TABLE_NAME),
                       (vector_tiles_table_name,))

        rows = cursor.fetchall()
        # no results
        if rows is None:
            return []

        # get the results
        return [VectorLayersEntry(id=row['id'],
                                  table_name=row['table_name'],
                                  name=row['name'],
                                  description=row['description'],
                                  min_zoom=row['minzoom'],
                                  max_zoom=row['maxzoom']) for row in rows]

    @staticmethod
    def insert_or_update_vector_tile_layer_entry(cursor,
                                                 vector_tile_layer_entry):
        """
        Adds an entry to the Vector Tiles Layers Table (gpkgext_vt_layers) with the values given

        :param cursor: the cursor to the GeoPackage database's connection
        :type cursor: Cursor

        :param vector_tile_layer_entry: the vector tile layer entry to be added to the table
        :type vector_tile_layer_entry: VectorLayersEntry

        :return Updated VectorLayerEntry with the id value populated
        """
        if not table_exists(cursor, GEOPACKAGE_VECTOR_LAYERS_TABLE_NAME):
            raise ValueError("Cannot add to {table} because {table} does not exist. Be sure to create the default "
                             "vector-tiles tables before calling this method."
                             .format(table=GEOPACKAGE_VECTOR_LAYERS_TABLE_NAME))

        cursor.execute("""
                          INSERT OR REPLACE INTO {table_name} (table_name,
                                                               name,
                                                               description,
                                                               minzoom,
                                                               maxzoom)
                          VALUES (?, ?, ?, ?, ?);
                       """.format(table_name=GEOPACKAGE_VECTOR_LAYERS_TABLE_NAME), (vector_tile_layer_entry.table_name,
                                                                                    vector_tile_layer_entry.name,
                                                                                    vector_tile_layer_entry.description,
                                                                                    vector_tile_layer_entry.min_zoom,
                                                                                    vector_tile_layer_entry.max_zoom))

        vector_tile_layer_entry.id = cursor.lastrowid
        return vector_tile_layer_entry

    @staticmethod
    def get_vector_tile_layer_entry_with_values(cursor,
                                                table_name,
                                                name,
                                                description,
                                                min_zoom,
                                                max_zoom):
        """
        searches the Vector Tiles Layers Table (gpkgext_vt_layers) for an entry(or entries) with the values given.
        Returns a VectorLayerEntry object if a match was found, None otherwise

        :param cursor: the cursor to the GeoPackage database's connection
        :type cursor: Cursor

        :param table_name: the value of the table_name column value (name of the vector tiles table)
        :type table_name: str, None

        :param name: the value of the name column value (the name of the layer)
        :type name: str

        :param description: the optional description column value
        :type description: str, None

        :param min_zoom: the optional min zoom column value
        :type min_zoom: int, None

        :param max_zoom: the optional max zoom column value
        :type max_zoom: int, None

        :return: VectorLayersEntry with all values populated or None if no matches were found in the table
        :rtype: VectorLayersEntry, None
        """
        if not table_exists(cursor, GEOPACKAGE_VECTOR_LAYERS_TABLE_NAME):
            raise ValueError("Table {table_name} doesn't exist.".format(table_name=GEOPACKAGE_VECTOR_LAYERS_TABLE_NAME))

        rows = select_query(cursor=cursor,
                            table_name=GEOPACKAGE_VECTOR_LAYERS_TABLE_NAME,
                            select_columns=['table_name', 'name', 'description', 'minzoom', 'maxzoom', 'id'],
                            where_columns_dictionary={'table_name': table_name,
                                                      'name': name,
                                                      'description': description,
                                                      'minzoom': min_zoom,
                                                      'maxzoom': max_zoom})
        if rows is None:
            return []

        # set the layer id
        return [VectorLayersEntry(id=row['id'],
                                  table_name=row['table_name'],
                                  name=row['name'],
                                  description=row['description'],
                                  min_zoom=row['minzoom'],
                                  max_zoom=row['maxzoom']) for row in rows]
