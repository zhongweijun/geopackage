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
from scripts.geopackage.extensions.geopackage_extensions import GeoPackageExtensions
from scripts.geopackage.extensions.vector_tiles.geopackage_vector_tiles import GeoPackageVectorTiles
from scripts.geopackage.extensions.vector_tiles.vector_tiles_content_entry import VectorTilesContentEntry
from scripts.geopackage.tiles.geopackage_abstract_tiles import GeoPackageAbstractTiles
from sqlite3 import Cursor, Binary

GEOPACKGE_GEOJSON_VECTOR_TILES_EXTENSION_NAME = "im_vector_tiles_geojson"


class GeoPackageGeoJSONVectorTiles(GeoPackageVectorTiles):
    """
    GeoPackage Tiles GeoJSON encoded vector tiles extension. Represents the im_vector_tiles_geojson extension.  Creates
    vector-tile pyramid user data tables where the tile_data column is encoded in GeoJSON
    """

    @staticmethod
    def insert_vector_layers_and_fields_from_tile_data(tile_data, table_name):
        """
        Reads the vector tiles data and extracts the Vector Layers and Fields from the GeoJSON encoded data.

        :param tile_data: the GeoJSON data to extract the information from
        :type tile_data: Binary

        :param table_name: the vector tiles layer name
        :type table_name: str
        :return:
        """
        # TODO implment this!
        return [], []

    def __init__(self,
                 vector_tiles_table_name):
        """
        Constructor

        :param vector_tiles_table_name: The table name of the vector-tiles table that has GeoJSON encoding for the
        tile_data column
        """
        super(GeoPackageGeoJSONVectorTiles, self).__init__(vector_tiles_table_name)

    @staticmethod
    def create_pyramid_user_data_table(cursor,
                                       tile_content):
        """
        Creates the vector-tile pyramid user data table with tile_data encoded in GeoJSON format. It will also register
        the extension in the GeoPackage.

        :param cursor: the cursor to the GeoPackage database's connection
        :type cursor: Cursor

        :param tile_content: The TileSet entry in the gpkg_contents table describing the vector-tiles in the GeoPackage
        :type tile_content: VectorTilesContentEntry
        """
        GeoPackageGeoJSONVectorTiles.create_default_tiles_tables(cursor=cursor)

        GeoPackageAbstractTiles.create_pyramid_user_data_table(cursor=cursor,
                                                               tiles_content=tile_content)

        GeoPackageExtensions.insert_or_update_extensions_row(cursor=cursor,
                                                             extension=
                                                             GeoPackageGeoJSONVectorTiles(tile_content.table_name))

    extension_name = GEOPACKGE_GEOJSON_VECTOR_TILES_EXTENSION_NAME

