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
from scripts.geopackage.core.content_entry import ContentEntry
from scripts.geopackage.core.geopackage_core import GeoPackageCore
from scripts.geopackage.srs.mercator import Mercator
from scripts.geopackage.tiles.tiles_content_entry import TilesContentEntry
from scripts.geopackage.utility.sql_utility import get_database_connection


class TestGeoPackageCore(object):

    def test_insert_srs_without_table(self, make_gpkg):
        gpkg = make_gpkg

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()
            with raises(ValueError):
                GeoPackageCore.insert_spatial_reference_system_row(cursor=cursor,
                                                                   spatial_reference_system=Mercator())

    def test_insert_contents_without_table(self, make_gpkg):
        gpkg = make_gpkg

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()
            tiles_entry = TilesContentEntry(table_name="table",
                                            identifier="id",
                                            min_y=0,
                                            min_x=0,
                                            max_x=0,
                                            max_y=0,
                                            srs_id=0)
            GeoPackageCore.insert_or_update_content(cursor=cursor,
                                                    content=tiles_entry)

    def test_get_all_content_entries(self, make_gpkg):

        gpkg = make_gpkg
        gpkg.initialize()

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()

            content1 = ContentEntry(table_name="tiles",
                                    data_type="tiles",
                                    identifier="idennntititi",
                                    min_x=0,
                                    min_y=1.0,
                                    max_x=2.2,
                                    max_y=3.3,
                                    srs_id=4326)
            GeoPackageCore.insert_or_update_content(cursor=cursor,
                                                    content=content1)
            content2 = ContentEntry(table_name="1231table",
                                    data_type="tiles",
                                    identifier="ddeentntity",
                                    min_x=4.7,
                                    min_y=3.2,
                                    max_x=2.1,
                                    max_y=1.1,
                                    srs_id=3857)
            GeoPackageCore.insert_or_update_content(cursor=cursor,
                                                    content=content2)

            actual_content1 = GeoPackageCore.get_content_entry_by_table_name(cursor=cursor,
                                                                             table_name=content1.table_name)

            TestGeoPackageCore.assert_content_entries_equal(expected_content_entry=content1,
                                                            actual_content_entry=actual_content1)

            actual_content2 = GeoPackageCore.get_content_entry_by_table_name(cursor=cursor,
                                                                             table_name=content2.table_name)

            TestGeoPackageCore.assert_content_entries_equal(expected_content_entry=content2,
                                                            actual_content_entry=actual_content2)

            all_entries = GeoPackageCore.get_all_content_entries(cursor=cursor)
            assert len(all_entries) == 2

    def test_get_all_content_entries_empty(self, make_gpkg):
        gpkg = make_gpkg

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()
            assert len(GeoPackageCore.get_all_content_entries(cursor=cursor)) == 0

        gpkg.initialize()
        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()
            assert len(GeoPackageCore.get_all_content_entries(cursor=cursor)) == 1

    def test_get_content_by_table_name_empty(self, make_gpkg):
        gpkg = make_gpkg

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()
            assert GeoPackageCore.get_content_entry_by_table_name(cursor=cursor,
                                                                  table_name="tiles") is None

        gpkg.initialize()
        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()
            assert GeoPackageCore.get_content_entry_by_table_name(cursor=cursor,
                                                                  table_name="Dont_Exist") is None

    def test_all_spatial_reference_system_entries_empty(self, make_gpkg):
        gpkg = make_gpkg

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()
            assert len(GeoPackageCore.get_all_spatial_reference_system_entries(cursor=cursor)) == 0

    @staticmethod
    def assert_content_entries_equal(expected_content_entry,
                                     actual_content_entry):
        """

        :param expected_content_entry:
        :type expected_content_entry: Content
        :param actual_content_entry:
        :type actual_content_entry: Content
        """
        assert expected_content_entry.table_name == actual_content_entry.table_name and \
               expected_content_entry.srs_id == actual_content_entry.srs_id and \
               expected_content_entry.min_x == actual_content_entry.min_x and \
               expected_content_entry.min_y == actual_content_entry.min_y and \
               expected_content_entry.max_y == actual_content_entry.max_y and \
               expected_content_entry.max_x == actual_content_entry.max_x and \
               expected_content_entry.data_type == actual_content_entry.data_type
