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
Date: 2018-11-11
   Requires: sqlite3, argparse
   Optional: Python Imaging Library (PIL or Pillow)
Credits:
  MapProxy imaging functions: http://mapproxy.org
  gdal2mb on github: https://github.com/developmentseed/gdal2mb

Version:
"""

from scripts.geopackage.core.geopackage_core import GeoPackageCore
from scripts.geopackage.geopackage import DEFAULT_TILES_IDENTIFIER
from scripts.geopackage.tiles.geopackage_tiles import GeoPackageTiles
from scripts.geopackage.tiles.tiles_content_entry import TilesContentEntry
from scripts.geopackage.utility.sql_utility import get_database_connection

try:
    from cStringIO import StringIO as ioBuffer
except ImportError:
    from io import BytesIO as ioBuffer
from sys import version_info
from uuid import uuid4

if version_info[0] == 3:
    xrange = range

from os.path import join

try:
    from PIL.Image import open as IOPEN
except ImportError:
    IOPEN = None


class TempDB(object):
    """
    Returns a temporary sqlite database to hold tiles for async workers.
    Has a <filename>.gpkg.part file format.
    """

    def __enter__(self):
        """With-statement caller."""
        return self

    def __init__(self,
                 filename,
                 tiles_table_name,
                 tiles_identifier=DEFAULT_TILES_IDENTIFIER):
        """
        Constructor.

        Inputs:
        filename -- the filename this database will be created with
        :param tiles_identifier:
        :param tiles_table_name:
        """
        uid = uuid4()
        self.name = uid.hex + '.gpkg.part'
        self.__file_path = join(filename, self.name)
        self.__db_con = get_database_connection(self.__file_path)
        self.tiles_table_name = tiles_table_name

        with self.__db_con as db_con:
            cursor = db_con.cursor()
            GeoPackageCore.create_core_tables(cursor)
            # TODO re-purpose this class to also accept vector tiles
            GeoPackageTiles.create_pyramid_user_data_table(cursor=cursor,
                                                           tiles_content=TilesContentEntry(table_name=
                                                                                           self.tiles_table_name,
                                                                                           identifier=
                                                                                           tiles_identifier,
                                                                                           min_x=0,
                                                                                           min_y=0,
                                                                                           max_x=0,
                                                                                           max_y=0,
                                                                                           srs_id=0))
            db_con.commit()
            # Enable pragma for fast sqlite creation
            cursor.execute("pragma synchronous = off;")
            cursor.execute("pragma journal_mode = off;")
            cursor.execute("pragma page_size = 80000;")
            cursor.execute("pragma foreign_keys = 1;")

    def execute(self, statement, inputs=None):
        with self.__db_con as db_con:
            cursor = db_con.cursor()
            if inputs is not None:
                result_cursor = cursor.execute(statement, inputs)
            else:
                result_cursor = cursor.execute(statement)
            return result_cursor

    def insert_image_blob(self, z, x, y, data):
        """
        Inserts a binary data array containing an image into a sqlite3
        database.

        Inputs:
        z -- the zoom level of the binary data
        x -- the row number of the data
        y -- the column number of the data
        data -- the image data containing in a binary array
        """
        gpkg_tiles = GeoPackageTiles()
        with self.__db_con as db_con:
            cursor = db_con.cursor()
            gpkg_tiles.insert_or_update_tile_data(cursor=cursor,
                                                  table_name=self.tiles_table_name,
                                                  zoom_level=z,
                                                  tile_column=x,
                                                  tile_row=y,
                                                  tile_data=data)

    def __exit__(self, type, value, traceback):
        """Resource cleanup on destruction."""
        self.__db_con.close()
