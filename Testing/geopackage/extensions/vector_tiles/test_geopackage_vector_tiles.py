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
from os.path import join, dirname
from sqlite3 import Binary

from Testing import resources
from Testing.test_tiles2gpkg import make_gpkg
from scripts.geopackage.core.geopackage_core import GeoPackageCore
from scripts.geopackage.extensions.geopackage_extensions import GEOPACKAGE_EXTENSIONS_TABLE_NAME, GeoPackageExtensions
from scripts.geopackage.extensions.vector_tiles.geopackage_mapbox_vector_tiles import GeoPackageMapBoxVectorTiles
from scripts.geopackage.extensions.vector_tiles.vector_fields.geopackage_vector_fields import GeoPackageVectorFields
from scripts.geopackage.extensions.vector_tiles.vector_fields.vector_fields_entry import VectorFieldType
from scripts.geopackage.extensions.vector_tiles.vector_layers.geopackage_vector_layers import GeoPackageVectorLayers
from scripts.geopackage.extensions.vector_tiles.vector_tiles_constants import GEOPACKAGE_VECTOR_LAYERS_TABLE_NAME, \
    GEOPACKAGE_VECTOR_FIELDS_TABLE_NAME
from scripts.geopackage.extensions.vector_tiles.vector_tiles_content_entry import VectorTilesContentEntry
from scripts.geopackage.tiles.geopackage_abstract_tiles import GEOPACKAGE_TILE_MATRIX_SET_TABLE_NAME, \
    GEOPACKAGE_TILE_MATRIX_TABLE_NAME
from scripts.geopackage.utility.sql_utility import get_database_connection, table_exists


class TestGeoPackageVectorTiles(object):

    @staticmethod
    def get_tile_data():
        with open(join(dirname(resources.__file__),
                       "tile_data.pbf"),
                  'rb') as in_file:
            data = in_file.read()
            in_file.close()
            return Binary(data)

    def test_map_box_vector_tiles_adding(self, make_gpkg):
        gpkg = make_gpkg

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()
            GeoPackageCore.create_core_tables(cursor=cursor)
            vector_tiles_content = VectorTilesContentEntry(table_name="vector-tiles-table",
                                                           identifier="identifier",
                                                           min_x=0,
                                                           max_x=1,
                                                           min_y=2,
                                                           max_y=3,
                                                           srs_id=4326)

            gpkg_mapbox = GeoPackageMapBoxVectorTiles(vector_tiles_table_name=vector_tiles_content.table_name)
            gpkg_mapbox.insert_or_update_vector_tiles_table(cursor=cursor,
                                                            vector_tiles_content=vector_tiles_content)

            # check to make sure the vector tiles are in the contents table
            content_returned = GeoPackageCore.get_content_entry_by_table_name(cursor=cursor,
                                                                              table_name=vector_tiles_content.table_name)
            assert vector_tiles_content.table_name == content_returned.table_name and \
                   vector_tiles_content.identifier == content_returned.identifier and \
                   vector_tiles_content.data_type == content_returned.data_type and \
                   vector_tiles_content.max_x == content_returned.max_x and \
                   vector_tiles_content.min_x == content_returned.min_x and \
                   vector_tiles_content.max_y == content_returned.max_y and \
                   vector_tiles_content.min_y == content_returned.min_y and \
                   vector_tiles_content.srs_id == content_returned.srs_id

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
                                table_name=vector_tiles_content.table_name)

            # check that the extensions rows were added
            assert GeoPackageExtensions.has_extension(cursor=cursor,
                                                      extension=GeoPackageVectorLayers())

            assert GeoPackageExtensions.has_extension(cursor=cursor,
                                                      extension=GeoPackageVectorFields())

            assert GeoPackageExtensions.has_extension(cursor=cursor,
                                                      extension=gpkg_mapbox)

            zoom_level = 13
            tile_row = 4921
            tile_column = 3313
            tile_data = TestGeoPackageVectorTiles.get_tile_data()

            gpkg_mapbox.insert_or_update_tile_data(cursor=cursor,
                                                   table_name=vector_tiles_content.table_name,
                                                   zoom_level=zoom_level,
                                                   tile_row=tile_row,
                                                   tile_column=tile_column,
                                                   tile_data=tile_data)

            # check if the tile data was added properly
            returned_tile_data = gpkg_mapbox.get_tile_data(cursor=cursor,
                                                           table_name=vector_tiles_content.table_name,
                                                           zoom_level=zoom_level,
                                                           tile_row=tile_row,
                                                           tile_column=tile_column)

            assert returned_tile_data == tile_data

            # check if the mapbox layers and field entries were extracted and added to the layers table
            vector_layer_entries = GeoPackageVectorLayers.get_vector_layer_entries_by_table_name(cursor=cursor,
                                                                                                 vector_tiles_table_name
                                                                                                 =vector_tiles_content
                                                                                                 .table_name)

            assert len(vector_layer_entries) == 2

            assert any(vector_layer_entry.table_name == vector_tiles_content.table_name and
                       vector_layer_entry.name == 'AgricultureSrf'
                       for vector_layer_entry
                       in vector_layer_entries)

            assert any(vector_layer_entry.table_name == vector_tiles_content.table_name and
                       vector_layer_entry.name == 'TransportationGroundCrv'
                       for vector_layer_entry
                       in vector_layer_entries)

            # check the field entries too
            vector_field_entries = GeoPackageVectorFields.get_vector_field_entry_by_values(cursor=cursor,
                                                                                           id=None,
                                                                                           name='Feature ID',
                                                                                           type=VectorFieldType.NUMBER,
                                                                                           layer_id=None)

            assert len(vector_field_entries) == 2

