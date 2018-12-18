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
from pytest import raises

from Testing.test_tiles2gpkg import make_gpkg
from scripts.geopackage.core.geopackage_core import GeoPackageCore, GEOPACKAGE_CONTENTS_TABLE_NAME
from scripts.geopackage.extensions.extension import Extension, EXTENSION_READ_WRITE_SCOPE, EXTENSION_WRITE_ONLY_SCOPE
from scripts.geopackage.extensions.geopackage_extensions import GeoPackageExtensions
from scripts.geopackage.tiles.geopackage_tiles import GeoPackageTiles
from scripts.geopackage.tiles.tiles_content_entry import TilesContentEntry
from scripts.geopackage.utility.sql_utility import get_database_connection


# noinspection PyClassHasNoInit
class TestGeoPackageExtensions:

    def test_getting_all_extensions(self, make_gpkg):
        table_name = "table table"
        my_extension = Extension(table_name=table_name,
                                 column_name=None,
                                 extension_name="extension name name",
                                 definition="Defffinition",
                                 scope=EXTENSION_READ_WRITE_SCOPE)
        gpkg = make_gpkg
        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()

            empty_extensions = GeoPackageExtensions.get_all_extensions(cursor=cursor)
            assert len(empty_extensions) == 0

            # need to create the table to exist
            GeoPackageCore.create_core_tables(cursor=cursor)
            GeoPackageTiles.create_pyramid_user_data_table(cursor=cursor,
                                                           tiles_content=TilesContentEntry(table_name=table_name,
                                                                                           identifier="Some identifier",
                                                                                           min_x=0,
                                                                                           min_y=0,
                                                                                           max_x=0,
                                                                                           max_y=0,
                                                                                           srs_id=0))
            GeoPackageExtensions.insert_or_update_extensions_row(cursor=cursor,
                                                                 extension=my_extension)

            one_extension = GeoPackageExtensions.get_all_extensions(cursor)

            assert len(one_extension) == 1

            assert one_extension[0].table_name == my_extension.table_name and \
                   one_extension[0].column_name == my_extension.column_name and \
                   one_extension[0].extension_name == my_extension.extension_name and \
                   one_extension[0].definition == my_extension.definition

    def test_getting_multiple_all_extensions(self, make_gpkg):
        my_extension = Extension(table_name="table table",
                                 column_name="id",
                                 extension_name="extension name name",
                                 definition="Defffinition",
                                 scope=EXTENSION_READ_WRITE_SCOPE)

        my_extension2 = Extension(table_name=None,
                                  column_name=None,
                                  extension_name="other extension name",
                                  definition="definition2",
                                  scope=EXTENSION_WRITE_ONLY_SCOPE)
        gpkg = make_gpkg
        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()
            # check to see if the table is currently empty
            empty_extensions = GeoPackageExtensions.get_all_extensions(cursor=cursor)
            assert len(empty_extensions) == 0

            # need to create the table to exist
            GeoPackageCore.create_core_tables(cursor=cursor)
            GeoPackageTiles.create_pyramid_user_data_table(cursor=cursor,
                                                           tiles_content=TilesContentEntry(table_name=my_extension
                                                                                           .table_name,
                                                                                           identifier="Some identifier",
                                                                                           min_x=0,
                                                                                           min_y=0,
                                                                                           max_x=0,
                                                                                           max_y=0,
                                                                                           srs_id=0))
            # add the first extension
            GeoPackageExtensions.insert_or_update_extensions_row(cursor=cursor,
                                                                 extension=my_extension)
            # check to see if one extension is in the table
            one_extension = GeoPackageExtensions.get_all_extensions(cursor)

            assert len(one_extension) == 1

            # add the second extension
            GeoPackageExtensions.insert_or_update_extensions_row(cursor=cursor,
                                                                 extension=my_extension2)

            # check to see if there are two extensions in the table
            two_extensions = GeoPackageExtensions.get_all_extensions(cursor=cursor)

            assert len(two_extensions) == 2

            # check if the values of the two extensions are valid
            assert two_extensions[0].table_name == my_extension.table_name and \
                   two_extensions[0].column_name == my_extension.column_name and \
                   two_extensions[0].extension_name == my_extension.extension_name and \
                   two_extensions[0].definition == my_extension.definition and \
                   two_extensions[1].table_name == my_extension2.table_name and \
                   two_extensions[1].column_name == my_extension2.column_name and \
                   two_extensions[1].extension_name == my_extension2.extension_name and \
                   two_extensions[1].definition == my_extension2.definition

    def test_empty_extensions(self, make_gpkg):
        gpkg = make_gpkg

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()
            # tests to make sure if table is created that the list to get extensions is still empty
            GeoPackageExtensions.create_extensions_table(cursor=cursor)

            # checks to make sure list is empty
            empty_extensions = GeoPackageExtensions.get_all_extensions(cursor=cursor)
            assert len(empty_extensions) == 0

    def test_table_needs_to_exist_exception(self, make_gpkg):
        gpkg = make_gpkg

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()
            with raises(ValueError):
                GeoPackageExtensions.insert_or_update_extensions_row(cursor=cursor,
                                                                     extension=Extension(table_name="Non_Existent_Table",
                                                                                         column_name=None,
                                                                                         extension_name="extension name",
                                                                                         definition="definition",
                                                                                         scope=EXTENSION_READ_WRITE_SCOPE))


    def test_column_needs_to_exist_exception(self, make_gpkg):
        gpkg = make_gpkg

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()
            GeoPackageCore.create_core_tables(cursor=cursor)
            with raises(ValueError):
                GeoPackageExtensions.insert_or_update_extensions_row(cursor=cursor,
                                                                     extension=Extension(table_name=GEOPACKAGE_CONTENTS_TABLE_NAME,
                                                                                         column_name="non-existent-column",
                                                                                         extension_name="extension name",
                                                                                         definition="definition",
                                                                                         scope=EXTENSION_READ_WRITE_SCOPE))
