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

Authors:
    Steven D. Lander, Reinventing Geospatial Inc (RGi)
    Jenifer Cochran, Reinventing Geospatial Inc (RGi)
Date: 2018-11-11
   Requires: sqlite3, argparse
   Optional: Python Imaging Library (PIL or Pillow)
Credits:
  MapProxy imaging functions: http://mapproxy.org
  gdal2mb on github: https://github.com/developmentseed/gdal2mb

Version:
"""
from abc import abstractmethod
from sqlite3 import Cursor, Binary

from scripts.geopackage.core.geopackage_core import GeoPackageCore
from scripts.geopackage.tiles.tile_matrix_set_entry import TileMatrixSetEntry
from scripts.geopackage.tiles.tiles_content_entry import TilesContentEntry
from scripts.geopackage.utility.sql_utility import table_exists, select_query

GEOPACKAGE_TILE_MATRIX_TABLE_NAME = "gpkg_tile_matrix"
GEOPACKAGE_TILE_MATRIX_SET_TABLE_NAME = "gpkg_tile_matrix_set"


class GeoPackageAbstractTiles(object):
    """
    'Tiles' subsystem of the GeoPackage implementation.  Responsible for the gpkg_tile_matrix, gpkg_tile_matrix_set, and
    user pyramid data tables.
    """

    def __init__(self):
        """
        Constructor
        """
        super(GeoPackageAbstractTiles, self).__init__()

    @staticmethod
    def create_gpkg_tile_matrix(cursor):
        """
        Creates the gpkg_tile_matrix table documents the structure of the tile matrix at each zoom level in each tiles
        table. It allows GeoPackages to contain rectangular as well as square tiles (e.g. for better representation of
        polar regions). It allows tile pyramids with zoom levels that differ in resolution by factors of 2, irregular
        intervals, or regular intervals other than factors of 2.

        :param cursor: the cursor to the GeoPackage database's connection
        :type cursor: Cursor
        """
        cursor.execute("""
               CREATE TABLE IF NOT EXISTS {table_name}
               (table_name    TEXT    NOT NULL, -- Tile Pyramid User Data Table Name
                zoom_level    INTEGER NOT NULL, -- 0 <= zoom_level <= max_level for table_name
                matrix_width  INTEGER NOT NULL, -- Number of columns (>= 1) in tile matrix at this zoom level
                matrix_height INTEGER NOT NULL, -- Number of rows (>= 1) in tile matrix at this zoom level
                tile_width    INTEGER NOT NULL, -- Tile width in pixels (>= 1) for this zoom level
                tile_height   INTEGER NOT NULL, -- Tile height in pixels (>= 1) for this zoom level
                pixel_x_size  DOUBLE  NOT NULL, -- In t_table_name srid units or default meters for srid 0 (>0)
                pixel_y_size  DOUBLE  NOT NULL, -- In t_table_name srid units or default meters for srid 0 (>0)
                CONSTRAINT pk_ttm PRIMARY KEY (table_name, zoom_level), CONSTRAINT fk_tmm_table_name FOREIGN KEY (table_name) REFERENCES gpkg_contents(table_name))
             """.format(table_name=GEOPACKAGE_TILE_MATRIX_TABLE_NAME))

    @staticmethod
    def create_gpkg_tile_matrix_set(cursor):
        """
        Creates the gpkg_tile_matrix_set table defines the spatial reference system (srs_id) and the maximum bounding
        box (min_x, min_y, max_x, max_y) for all possible tiles in a tile pyramid user data table.

        :param cursor: the cursor to the GeoPackage database's connection
        :type cursor: Cursor
        """
        cursor.execute("""
               CREATE TABLE IF NOT EXISTS {table_name}
               (table_name TEXT    NOT NULL PRIMARY KEY, -- Tile Pyramid User Data Table Name
                srs_id     INTEGER NOT NULL,             -- Spatial Reference System ID: gpkg_spatial_ref_sys.srs_id
                min_x      DOUBLE  NOT NULL,             -- Bounding box minimum easting or longitude for all content in table_name
                min_y      DOUBLE  NOT NULL,             -- Bounding box minimum northing or latitude for all content in table_name
                max_x      DOUBLE  NOT NULL,             -- Bounding box maximum easting or longitude for all content in table_name
                max_y      DOUBLE  NOT NULL,             -- Bounding box maximum northing or latitude for all content in table_name
                CONSTRAINT fk_gtms_table_name FOREIGN KEY (table_name) REFERENCES gpkg_contents(table_name), CONSTRAINT fk_gtms_srs FOREIGN KEY (srs_id) REFERENCES gpkg_spatial_ref_sys (srs_id))
             """.format(table_name=GEOPACKAGE_TILE_MATRIX_SET_TABLE_NAME))

    @staticmethod
    @abstractmethod
    def create_default_tiles_tables(cursor):
        """
        Creates the default relational tables for the pyramid-user-data table (i.e. gpkg_tile_matrix, gpkg_tile_matrix_set etc..)
        :param cursor:  the cursor to the GeoPackage database's connection
        """
        raise NotImplementedError()

    @staticmethod
    def create_pyramid_user_data_table(cursor,
                                       tiles_content):
        """
        Creates the tile pyramid user data table containing the tile data. "Tile pyramid" refers to the concept of
        pyramid structure of tiles of different spatial extent and resolution at different zoom levels, and the tile
        data itself. "Tile" refers to an individual raster image such as a PNG or JPEG that covers a specific geographic
        area.

        :param cursor: the cursor to the GeoPackage database's connection
        :type cursor: Cursor

        :param tiles_content: The TileSet entry in the gpkg_contents table describing the tiles in the GeoPackage
        :type tiles_content: TilesContentEntry
        """

        # TODO create the default tiles tables too? -how to know which tiles encoding was used to call the right method?

        if table_exists(cursor=cursor,
                        table_name=tiles_content.table_name):
            raise ValueError("Table {table_name} already exists! Cannot create another table by the same name."
                             .format(table_name=tiles_content.table_name))

        # create the tiles table
        cursor.execute("""
                          CREATE TABLE IF NOT EXISTS "{table_name}" 
                          (id          INTEGER PRIMARY KEY AUTOINCREMENT, -- Autoincrement primary key
                           zoom_level  INTEGER NOT NULL,                  -- min(zoom_level) <= zoom_level <= max(zoom_level) for t_table_name
                           tile_column INTEGER NOT NULL,                  -- 0 to tile_matrix matrix_width - 1
                           tile_row    INTEGER NOT NULL,                  -- 0 to tile_matrix matrix_height - 1
                           tile_data   BLOB    NOT NULL,                  -- Of an image MIME type specified in clauses Tile Encoding PNG, Tile Encoding JPEG, Tile Encoding WEBP
                           UNIQUE (zoom_level, tile_column, tile_row))
                       """.format(table_name=tiles_content.table_name))

        # add to contents table
        GeoPackageCore.insert_or_update_content(cursor=cursor,
                                                content=tiles_content)

    @staticmethod
    def insert_or_udpate_gpkg_tile_matrix_row(cursor,
                                              table_name,
                                              zoom_level,
                                              matrix_width,
                                              matrix_height,
                                              tile_width,
                                              tile_height,
                                              pixel_x_size,
                                              pixel_y_size):
        """
        Inserts a new row or updates an existing row in the gpkg_tile_matrix Table. The gpkg_tile_matrix table documents
        the structure of the tile matrix at each zoom level in each tiles table. It allows GeoPackages to contain
        rectangular as well as square tiles (e.g. for better representation of polar regions). It allows tile pyramids
        with zoom levels that differ in resolution by factors of 2, irregular intervals, or regular intervals other than
        factors of 2.

        :param cursor: the cursor to the GeoPackage database's connection
        :type cursor: Cursor

        :param table_name: Tile Pyramid User Data Table Name
        :type table_name: str

        :param zoom_level:  0 <= zoom_level <= max_level for table_name
        :type zoom_level: int

        :param matrix_width: Number of columns (>= 1) in tile matrix at this zoom level
        :type matrix_width: int

        :param matrix_height: Number of rows (>= 1) in tile matrix at this zoom level,
        :type matrix_height: int

        :param tile_width: Tile width in pixels (>= 1)for this zoom level
        :type tile_width: int

        :param tile_height: Tile height in pixels (>= 1) for this zoom level
        :type tile_height: int

        :param pixel_x_size: In table_name srid units or default meters for srid 0 (>0)
        :type pixel_x_size: float

        :param pixel_y_size: In table_name srid units or default meters for srid 0 (>0)
        :type pixel_y_size: float
        """
        if not table_exists(cursor, GEOPACKAGE_TILE_MATRIX_TABLE_NAME):
            raise ValueError("Cannot add row to {table} because it does not exist"
                             .format(table=GEOPACKAGE_TILE_MATRIX_TABLE_NAME))
        tile_matrix_stmt = """
                              INSERT OR REPLACE INTO {table_name} (
                                       table_name,
                                       zoom_level,
                                       matrix_width,
                                       matrix_height,
                                       tile_width,
                                       tile_height,
                                       pixel_x_size,
                                       pixel_y_size)
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                           """.format(table_name=GEOPACKAGE_TILE_MATRIX_TABLE_NAME)

        cursor.execute(tile_matrix_stmt,
                       (table_name,
                        zoom_level,
                        matrix_width,
                        matrix_height,
                        tile_width,
                        tile_height,
                        pixel_x_size,
                        pixel_y_size))

    @staticmethod
    def insert_or_update_gpkg_tile_matrix_set_row(cursor,
                                                  tiles_content,
                                                  update_contents_table=True):

        """
        Inserts or updates the gpkg_tile_matrix_set Table with the following values. The gpkg_tile_matrix_set table
        defines the spatial reference system (srs_id) and the maximum bounding box (min_x, min_y, max_x, max_y) for all
        possible tiles in a tile pyramid user data table.

        :param cursor: the cursor to the GeoPackage database's connection
        :type cursor: Cursor

        :param tiles_content:  The TileSet entry in the gpkg_contents table describing the tiles in the GeoPackage
        :type tiles_content: TilesContentEntry

        :param update_contents_table: True if the gpkg_contents table should be updated as well with the same bounds,
        false otherwise
        :type update_contents_table: bool
        """
        if not table_exists(cursor, GEOPACKAGE_TILE_MATRIX_SET_TABLE_NAME):
            raise ValueError("Cannot add row to {table} because it does not exist"
                             .format(table=GEOPACKAGE_TILE_MATRIX_SET_TABLE_NAME))

        tile_matrix_set_stmt = """
                                   INSERT OR REPLACE INTO {table_name} 
                                      (table_name,
                                       srs_id,
                                       min_x,
                                       min_y,
                                       max_x,   
                                       max_y)
                                   VALUES (?, ?, ?, ?, ?, ?);
                               """.format(table_name=GEOPACKAGE_TILE_MATRIX_SET_TABLE_NAME)

        cursor.execute(tile_matrix_set_stmt,
                       (tiles_content.table_name,
                        tiles_content.srs_id,
                        tiles_content.min_x,
                        tiles_content.min_y,
                        tiles_content.max_x,
                        tiles_content.max_y))

        if update_contents_table:
            # update the contents table as well
            GeoPackageCore.insert_or_update_content(cursor=cursor,
                                                    content=tiles_content)

    def insert_or_update_tile_data(self,
                                   cursor,
                                   table_name,
                                   zoom_level,
                                   tile_column,
                                   tile_row,
                                   tile_data):
        """
        Inserts or updates row in the pyramid user data table with the table_name provided.

        :param cursor: the cursor to the GeoPackage database's connection
        :type cursor: Cursor

        :param table_name: Tile Pyramid User Data Table Name
        :type table_name: str

        :param zoom_level:  0 <= zoom_level <= max_level for table_name
        :type zoom_level: int

        :param tile_column:  0 to tile_matrix matrix_width - 1
        :type tile_column: int

        :param tile_row: 0 to tile_matrix matrix_height - 1
        :type tile_row: int

        :param tile_data: Of an image MIME type specified in clauses Tile Encoding PNG, Tile Encoding JPEG,
        [tile_enc_webp]
        :type tile_data: Binary
        """
        if not table_exists(cursor, table_name):
            raise ValueError("Cannot add row to {table} because it does not exist"
                             .format(table=table_name))

        image_blob_stmt = """
                              INSERT OR REPLACE INTO "{table_name}"
                                  (zoom_level, 
                                  tile_column, 
                                  tile_row, 
                                  tile_data)
                              VALUES (?,?,?,?);
                          """.format(table_name=table_name)
        cursor.execute(image_blob_stmt, (zoom_level,
                                         tile_column,
                                         tile_row,
                                         tile_data))

    @staticmethod
    def get_tile_data(cursor,
                      table_name,
                      zoom_level,
                      tile_column,
                      tile_row):
        """
        Returns the tile data at the specified zoom level, tile row, and tile column from the table given

        :param cursor: the cursor to the GeoPackage database's connection
        :type cursor: Cursor

        :param table_name: Tile Pyramid User Data Table Name
        :type table_name: str

        :param zoom_level:  0 <= zoom_level <= max_level for table_name
        :type zoom_level: int

        :param tile_column:  0 to tile_matrix matrix_width - 1
        :type tile_column: int

        :param tile_row: 0 to tile_matrix matrix_height - 1
        :type tile_row: int

        :return: the tile data at the specified zoom level, tile row, and tile column from the table given
        :rtype: Binary
        """

        rows = select_query(cursor=cursor,
                            table_name=table_name,
                            select_columns=['tile_data'],
                            where_columns_dictionary={'zoom_level': zoom_level,
                                                      'tile_column': tile_column,
                                                      'tile_row': tile_row})

        return None if rows is None or len(rows) < 1 else rows[0]['tile_data']

    @staticmethod
    def get_tile_matrix_set_entry_by_table_name(cursor, table_name):
        """
        Returns the Tile Matrix Set entry in the GeoPackage Tile Matrix Set table (gpkg_tile_matrix_set) where the
        table_name column matches the table_name passed in or None if none match

        :param cursor: the cursor to the GeoPackage database's connection
        :type cursor: Cursor

        :return  Returns the Tile Matrix Set entry in the GeoPackage Tile Matrix Set table (gpkg_tile_matrix_set) where the
        table_name column matches the table_name passed in or None if none match
        :rtype: TileMatrixSetEntry, None
        """
        if not table_exists(cursor, GEOPACKAGE_TILE_MATRIX_SET_TABLE_NAME):
            return None
            # select all the rows
        cursor.execute("SELECT * FROM {table_name} WHERE table_name = ?;"
                       .format(table_name=GEOPACKAGE_TILE_MATRIX_SET_TABLE_NAME),
                       (table_name,))

        row = cursor.fetchone()
        # no matches found
        if row is None:
            return None

        return TileMatrixSetEntry(table_name=row['table_name'],
                                  min_x=row['min_x'],
                                  min_y=row['min_y'],
                                  max_x=row['max_x'],
                                  max_y=row['max_y'],
                                  srs_id=row['srs_id'])
