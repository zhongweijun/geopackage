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
from scripts.geopackage.extensions.vector_tiles.geopackage_mapbox_vector_tiles import GeoPackageMapBoxVectorTiles
from scripts.geopackage.extensions.vector_tiles.vector_fields.geopackage_vector_fields import GeoPackageVectorFields
from scripts.geopackage.extensions.vector_tiles.vector_fields.vector_fields_entry import VectorFieldType, \
    VectorFieldsEntry
from scripts.geopackage.utility.sql_utility import get_database_connection


class TestGeoPackageVectorFields(object):

    def test_get_all_vector_entries_empty(self, make_gpkg):
        gpkg = make_gpkg

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()

            assert len(GeoPackageVectorFields.get_all_vector_fields_entries(cursor=cursor)) == 0

    def test_get_all_vector_entries_by_values_no_match(self, make_gpkg):
        gpkg = make_gpkg

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()

            assert len(GeoPackageVectorFields.get_vector_field_entry_by_values(cursor=cursor,
                                                                               id=None,
                                                                               layer_id=1,
                                                                               name="name",
                                                                               type=VectorFieldType.BOOLEAN)) == 0

    def test_get_all_vector_entries_by_values2(self, make_gpkg):
        gpkg = make_gpkg

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()

            vector_fields_entry = VectorFieldsEntry(layer_id=1,
                                                    name='field name',
                                                    field_type=VectorFieldType.BOOLEAN)
            GeoPackageMapBoxVectorTiles(vector_fields_entry.name).create_default_tiles_tables(cursor=cursor)
            GeoPackageVectorFields.insert_or_update_vector_tile_field_entry(cursor=cursor,
                                                                            vector_tiles_field_entry=vector_fields_entry)
            assert len(GeoPackageVectorFields.get_vector_field_entry_by_values(cursor=cursor,
                                                                               id=1,
                                                                               layer_id=1,
                                                                               name="name",
                                                                               type=VectorFieldType.BOOLEAN)) == 0

            assert len(GeoPackageVectorFields.get_vector_field_entry_by_values(cursor=cursor,
                                                                               id=None,
                                                                               layer_id=vector_fields_entry.layer_id,
                                                                               name=vector_fields_entry.name,
                                                                               type=vector_fields_entry.type)) == 1

    def test_insert_or_udpate_vector_field_entry_empty(self, make_gpkg):
        gpkg = make_gpkg

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()
            vector_fields_entry = VectorFieldsEntry(layer_id=1,
                                                    name='field name',
                                                    field_type=VectorFieldType.BOOLEAN)
            with raises(ValueError):
                GeoPackageVectorFields.insert_or_update_vector_tile_field_entry(cursor=cursor,
                                                                                vector_tiles_field_entry=
                                                                                vector_fields_entry)

    def test_get_all_vector_field_entries(self, make_gpkg):
        gpkg = make_gpkg

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()

            vector_fields_entry = VectorFieldsEntry(layer_id=1,
                                                    name='field name',
                                                    field_type=VectorFieldType.BOOLEAN)
            GeoPackageMapBoxVectorTiles(vector_fields_entry.name).create_default_tiles_tables(cursor=cursor)

            assert len(GeoPackageVectorFields.get_all_vector_fields_entries(cursor=cursor)) == 0

            GeoPackageVectorFields.insert_or_update_vector_tile_field_entry(cursor=cursor,
                                                                            vector_tiles_field_entry=vector_fields_entry)
            assert len(GeoPackageVectorFields.get_all_vector_fields_entries(cursor=cursor)) == 1

    def test_get_vector_field_entry_by_values_all_none_values(self, make_gpkg):
        gpkg = make_gpkg

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()
            GeoPackageVectorFields.create_vector_fields_table(cursor=cursor)
            with raises(ValueError):
                GeoPackageVectorFields.get_vector_field_entry_by_values(cursor=cursor)
