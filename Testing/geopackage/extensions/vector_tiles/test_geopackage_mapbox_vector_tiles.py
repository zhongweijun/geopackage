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
from scripts.geopackage.extensions.geopackage_extensions import GEOPACKAGE_EXTENSIONS_TABLE_NAME, GeoPackageExtensions
from scripts.geopackage.extensions.vector_tiles.geopackage_mapbox_vector_tiles import GeoPackageMapBoxVectorTiles
from scripts.geopackage.extensions.vector_tiles.vector_fields.geopackage_vector_fields import GeoPackageVectorFields
from scripts.geopackage.extensions.vector_tiles.vector_layers.geopackage_vector_layers import GeoPackageVectorLayers
from scripts.geopackage.extensions.vector_tiles.vector_tiles_constants import GEOPACKAGE_VECTOR_LAYERS_TABLE_NAME, \
    GEOPACKAGE_VECTOR_FIELDS_TABLE_NAME
from scripts.geopackage.extensions.vector_tiles.vector_tiles_content_entry import VectorTilesContentEntry
from scripts.geopackage.tiles.geopackage_abstract_tiles import GEOPACKAGE_TILE_MATRIX_SET_TABLE_NAME, \
    GEOPACKAGE_TILE_MATRIX_TABLE_NAME
from scripts.geopackage.utility.sql_utility import get_database_connection, table_exists


class TestGeoPackageMapBoxVectorTiles(object):

    def test_create_pyramid_user_data_table(self, make_gpkg):
        gpkg = make_gpkg

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()

            vector_tiles_entry = VectorTilesContentEntry(table_name='vect-tables',
                                                         identifier='I am a vector tiles table',
                                                         min_x=0.0,
                                                         min_y=1.0,
                                                         max_x=3.0,
                                                         max_y=4.0,
                                                         srs_id=4326)

            GeoPackageMapBoxVectorTiles.create_pyramid_user_data_table(cursor=cursor,
                                                                       tiles_content=vector_tiles_entry)

            # check if the default tiles tables were added
            assert table_exists(cursor=cursor,
                                table_name=GEOPACKAGE_TILE_MATRIX_SET_TABLE_NAME)

            assert table_exists(cursor=cursor,
                                table_name=GEOPACKAGE_TILE_MATRIX_TABLE_NAME)
            # check if the vector-tiles tables were added
            assert table_exists(cursor=cursor,
                                table_name=GEOPACKAGE_VECTOR_LAYERS_TABLE_NAME)

            assert table_exists(cursor=cursor,
                                table_name=GEOPACKAGE_VECTOR_FIELDS_TABLE_NAME)

            assert table_exists(cursor=cursor,
                                table_name=GEOPACKAGE_EXTENSIONS_TABLE_NAME)

            assert table_exists(cursor=cursor,
                                table_name=vector_tiles_entry.table_name)

            # check that the extensions rows were added
            assert GeoPackageExtensions.has_extension(cursor=cursor,
                                                      extension=GeoPackageVectorLayers())

            assert GeoPackageExtensions.has_extension(cursor=cursor,
                                                      extension=GeoPackageVectorFields())

            assert GeoPackageExtensions.has_extension(cursor=cursor,
                                                      extension=GeoPackageMapBoxVectorTiles(vector_tiles_table_name=
                                                                                            vector_tiles_entry
                                                                                            .table_name))
