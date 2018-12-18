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
from scripts.geopackage.core.geopackage_core import GeoPackageCore, GEOPACKAGE_SPATIAL_REFERENCE_SYSTEM_TABLE_NAME
from scripts.geopackage.extensions.metadata.metadata_reference.geopackage_metadata_reference import \
    GeoPackageMetadataReference
from scripts.geopackage.extensions.metadata.metadata_reference.metadata_reference import MetadataReference
from scripts.geopackage.extensions.metadata.metadata_reference.reference_scope import ReferenceScope
from scripts.geopackage.utility.sql_utility import get_database_connection


class TestGeoPackageMetadataReference(object):

    def test_invalid_table_name_reference(self, make_gpkg):
        gpkg = make_gpkg

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()
            with raises(ValueError):
                metadata_reference = MetadataReference(table_name="Non-existent-table",
                                                       reference_scope=ReferenceScope.TABLE,
                                                       column_name=None,
                                                       row_identifier=None,
                                                       file_identifier=0,
                                                       parent_identifier=None)
                GeoPackageMetadataReference.insert_or_update_metadata_reference_row(cursor=cursor,
                                                                                    metadata_reference=
                                                                                    metadata_reference)

    def test_invalid_column_name_reference(self, make_gpkg):
        gpkg = make_gpkg

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()
            # create the gpkg_contents table
            GeoPackageCore.create_core_tables(cursor=cursor)
            with raises(ValueError):
                metadata_reference = MetadataReference(table_name="gpkg_contents",
                                                       reference_scope=ReferenceScope.COLUMN,
                                                       column_name="non-existent-column",
                                                       row_identifier=None,
                                                       file_identifier=0,
                                                       parent_identifier=None)
                GeoPackageMetadataReference.insert_or_update_metadata_reference_row(cursor=cursor,
                                                                                    metadata_reference=
                                                                                    metadata_reference)

    def test_invalid_row_identifier_reference(self, make_gpkg):
        gpkg = make_gpkg

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()
            # create the gpkg_contents table
            GeoPackageCore.create_core_tables(cursor=cursor)
            with raises(ValueError):
                metadata_reference = MetadataReference(table_name=GEOPACKAGE_SPATIAL_REFERENCE_SYSTEM_TABLE_NAME,
                                                       reference_scope=ReferenceScope.ROW_COL,
                                                       column_name="srs_id",
                                                       row_identifier=18,  # non-existent rowid
                                                       file_identifier=0,
                                                       parent_identifier=None)
                GeoPackageMetadataReference.insert_or_update_metadata_reference_row(cursor=cursor,
                                                                                    metadata_reference=
                                                                                    metadata_reference)

    def test_valid_metadata_reference(self, make_gpkg):
        gpkg = make_gpkg

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()
            # create the gpkg_contents table
            GeoPackageCore.create_core_tables(cursor=cursor)
            metadata_reference = MetadataReference(table_name=GEOPACKAGE_SPATIAL_REFERENCE_SYSTEM_TABLE_NAME,
                                                   reference_scope=ReferenceScope.ROW_COL,
                                                   column_name="srs_id",
                                                   row_identifier=0,
                                                   file_identifier=0,
                                                   parent_identifier=None)
            GeoPackageMetadataReference.insert_or_update_metadata_reference_row(cursor=cursor,
                                                                                metadata_reference=metadata_reference)

            metadata_references = GeoPackageMetadataReference.get_all_metadata_references(cursor=cursor)

            assert len(metadata_references) == 1

            assert metadata_references[0].table_name == metadata_reference.table_name and \
                   metadata_references[0].reference_scope == metadata_reference.reference_scope and \
                   metadata_references[0].column_name == metadata_reference.column_name and \
                   metadata_references[0].row_identifier == metadata_reference.row_identifier and \
                   metadata_references[0].file_identifier == metadata_reference.file_identifier and \
                   metadata_references[0].parent_identifier == metadata_reference.parent_identifier

    def test_valid_empty_metadata_references(self, make_gpkg):
        gpkg = make_gpkg

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()
            metadata_references = GeoPackageMetadataReference.get_all_metadata_references(cursor=cursor)
            assert len(metadata_references) == 0
