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
from scripts.geopackage.extensions.vector_tiles.geopackage_geojson_vector_tiles import GeoPackageGeoJSONVectorTiles
from scripts.geopackage.extensions.vector_tiles.vector_layers.geopackage_vector_layers import GeoPackageVectorLayers
from scripts.geopackage.extensions.vector_tiles.vector_layers.vector_layers_entry import VectorLayersEntry
from scripts.geopackage.utility.sql_utility import get_database_connection


class TestGeoPackageVectorLayers(object):

    def test_all_vector_layer_entries_no_table(self, make_gpkg):
        gpkg = make_gpkg

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()

            vector_layer_entries = GeoPackageVectorLayers.get_all_vector_layers_entries(cursor=cursor)

            assert len(vector_layer_entries) == 0

    def test_all_vector_layer_entries_not_empty(self, make_gpkg):
        gpkg = make_gpkg

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()
            GeoPackageGeoJSONVectorTiles.create_default_tiles_tables(cursor=cursor)
            expected_layer_entry_1 = VectorLayersEntry(table_name="vector-table",
                                                       name='layer name',
                                                       description='my description',
                                                       min_zoom=3,
                                                       max_zoom=12)
            # add the vector layer entry to the table
            GeoPackageVectorLayers.insert_or_update_vector_tile_layer_entry(cursor=cursor,
                                                                            vector_tile_layer_entry=
                                                                            expected_layer_entry_1)
            # make sure the id has been updated
            assert expected_layer_entry_1.id is not None

            # test to see if the retrieval works
            vector_layer_entries = GeoPackageVectorLayers.get_all_vector_layers_entries(cursor=cursor)

            assert len(vector_layer_entries) == 1

            # check to see if the values are what is expected
            TestGeoPackageVectorLayers.assert_vector_layer_entries_are_equal(
                expected_vector_layer_entry=expected_layer_entry_1,
                actual_vector_layer_entry=vector_layer_entries[0])

    def test_all_vector_layer_entries_two_entries(self, make_gpkg):
        gpkg = make_gpkg

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()
            GeoPackageGeoJSONVectorTiles.create_default_tiles_tables(cursor=cursor)
            expected_layer_entry_1 = VectorLayersEntry(table_name="vector-table",
                                                       name='layer name',
                                                       description='my description',
                                                       min_zoom=3,
                                                       max_zoom=12)
            # add the vector layer entry to the table
            GeoPackageVectorLayers.insert_or_update_vector_tile_layer_entry(cursor=cursor,
                                                                            vector_tile_layer_entry=
                                                                            expected_layer_entry_1)
            # make sure the id has been updated
            assert expected_layer_entry_1.id is not None

            # test to see if the retrieval works
            vector_layer_entries = GeoPackageVectorLayers.get_all_vector_layers_entries(cursor=cursor)

            assert len(vector_layer_entries) == 1

            # check to see if the values are what is expected
            TestGeoPackageVectorLayers.assert_vector_layer_entries_are_equal(expected_layer_entry_1,
                                                                             vector_layer_entries[0])

            # add a second entry to the table
            expected_layer_entry_2 = VectorLayersEntry(table_name='vector-table2',
                                                       name='layer2',
                                                       description='mdsfa',
                                                       min_zoom=1,
                                                       max_zoom=18)

            GeoPackageVectorLayers.insert_or_update_vector_tile_layer_entry(cursor=cursor,
                                                                            vector_tile_layer_entry=
                                                                            expected_layer_entry_2)

            # make sure the id has been updated
            assert expected_layer_entry_2.id is not None

            # test to see if the retrieval works
            vector_layer_entries = GeoPackageVectorLayers.get_all_vector_layers_entries(cursor=cursor)

            assert len(vector_layer_entries) == 2

            # check to see if the values are what is expected
            TestGeoPackageVectorLayers.assert_vector_layer_entries_are_equal(
                expected_vector_layer_entry=expected_layer_entry_1,
                actual_vector_layer_entry=next(vector_layer_entry
                                               for vector_layer_entry
                                               in vector_layer_entries
                                               if vector_layer_entry.id ==
                                               expected_layer_entry_1.id))

            # check to see if the values are what is expected
            TestGeoPackageVectorLayers.assert_vector_layer_entries_are_equal(
                expected_vector_layer_entry=expected_layer_entry_2,
                actual_vector_layer_entry=next(vector_layer_entry
                                               for vector_layer_entry
                                               in vector_layer_entries
                                               if vector_layer_entry.id ==
                                               expected_layer_entry_2.id))

    def test_get_vector_layers_by_table_name_no_table(self, make_gpkg):
        gpkg = make_gpkg

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()

            vector_layer_entries = GeoPackageVectorLayers.get_vector_layer_entries_by_table_name(cursor=cursor,
                                                                                                 vector_tiles_table_name
                                                                                                 ='tablesss')

            assert len(vector_layer_entries) == 0

    def test_insert_or_update_no_table(self, make_gpkg):
        gpkg = make_gpkg

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()
            expected_layer_entry_1 = VectorLayersEntry(table_name="vector-table",
                                                       name='layer name',
                                                       description='my description',
                                                       min_zoom=3,
                                                       max_zoom=12)

            with raises(ValueError):
                GeoPackageVectorLayers.insert_or_update_vector_tile_layer_entry(cursor=cursor,
                                                                                vector_tile_layer_entry=
                                                                                expected_layer_entry_1)

    def test_get_vector_tile_layer_entry_with_values_no_table(self, make_gpkg):
        gpkg = make_gpkg

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()
            with raises(ValueError):
                GeoPackageVectorLayers.get_vector_tile_layer_entry_with_values(cursor=cursor,
                                                                               table_name='table',
                                                                               max_zoom=10,
                                                                               min_zoom=1,
                                                                               description='hi',
                                                                               name='asdfa')

    def test_get_vector_tile_layer_entry_with_values_not_empty(self, make_gpkg):
        gpkg = make_gpkg

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()
            vector_layer_entry = VectorLayersEntry(table_name='my_table',
                                                   name='nammm33',
                                                   min_zoom=None,
                                                   max_zoom=10,
                                                   description=None)
            GeoPackageGeoJSONVectorTiles.create_default_tiles_tables(cursor=cursor)
            GeoPackageVectorLayers.insert_or_update_vector_tile_layer_entry(cursor=cursor,
                                                                            vector_tile_layer_entry=vector_layer_entry)
            vector_layer_entries = GeoPackageVectorLayers.get_vector_tile_layer_entry_with_values(cursor=cursor,
                                                                                                  table_name=
                                                                                                  vector_layer_entry
                                                                                                  .table_name,
                                                                                                  max_zoom=
                                                                                                  vector_layer_entry
                                                                                                  .max_zoom,
                                                                                                  min_zoom=
                                                                                                  vector_layer_entry
                                                                                                  .min_zoom,
                                                                                                  description=
                                                                                                  vector_layer_entry
                                                                                                  .description,
                                                                                                  name=
                                                                                                  vector_layer_entry
                                                                                                  .name)
            assert len(vector_layer_entries) == 1

            TestGeoPackageVectorLayers.assert_vector_layer_entries_are_equal(
                actual_vector_layer_entry=vector_layer_entries[0],
                expected_vector_layer_entry=vector_layer_entry)

    @staticmethod
    def assert_vector_layer_entries_are_equal(expected_vector_layer_entry,
                                              actual_vector_layer_entry):
        assert expected_vector_layer_entry.name == actual_vector_layer_entry.name and \
               expected_vector_layer_entry.table_name == actual_vector_layer_entry.table_name and \
               expected_vector_layer_entry.min_zoom == actual_vector_layer_entry.min_zoom and \
               expected_vector_layer_entry.max_zoom == actual_vector_layer_entry.max_zoom and \
               expected_vector_layer_entry.description == actual_vector_layer_entry.description and \
               expected_vector_layer_entry.id == actual_vector_layer_entry.id
