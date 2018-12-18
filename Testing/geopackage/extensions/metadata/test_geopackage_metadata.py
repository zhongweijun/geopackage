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

from Testing.test_tiles2gpkg import make_gpkg
from scripts.geopackage.extensions.metadata.geopackage_metadata import GeoPackageMetadata
from scripts.geopackage.extensions.metadata.md_scope import MdScope
from scripts.geopackage.extensions.metadata.metadata import Metadata
from scripts.geopackage.utility.sql_utility import get_database_connection


class TestGeoPackageMetadata(object):

    def test_valid_metadata_reference(self, make_gpkg):
        gpkg = make_gpkg

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()

            metadata = Metadata(md_scope=MdScope.DATASET,
                                md_standard_uri='http://www.geopackage.org/spec121/#extension_metadata',
                                metadata="metadata")
            GeoPackageMetadata.insert_or_update_metadata_row(cursor=cursor,
                                                             metadata=metadata)

            metadatas = GeoPackageMetadata.get_all_metadata(cursor=cursor)

            assert len(metadatas) == 1

            assert metadatas[0].md_scope == metadata.md_scope and \
                   metadatas[0].md_standard_uri == metadata.md_standard_uri and \
                   metadatas[0].metadata == metadata.metadata and \
                   metadatas[0].mime_type == metadata.mime_type


    def test_valid_empty_list(self, make_gpkg):
        gpkg = make_gpkg

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()

            metadatas = GeoPackageMetadata.get_all_metadata(cursor=cursor)

            assert len(metadatas) == 0