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
from abc import abstractmethod, abstractproperty

from scripts.geopackage.extensions.extension import Extension, EXTENSION_READ_WRITE_SCOPE

from scripts.geopackage.extensions.geopackage_extensions import GeoPackageExtensions
from scripts.geopackage.extensions.vector_tiles.vector_fields.geopackage_vector_fields import GeoPackageVectorFields
from scripts.geopackage.extensions.vector_tiles.vector_layers.geopackage_vector_layers import GeoPackageVectorLayers
from scripts.geopackage.extensions.vector_tiles.vector_tiles_constants import VECTOR_TILES_DEFINITION
from scripts.geopackage.tiles.geopackage_abstract_tiles import GeoPackageAbstractTiles
from scripts.geopackage.tiles.geopackage_tiles import GeoPackageTiles
from scripts.geopackage.extensions.vector_tiles.vector_tiles_content_entry import VectorTilesContentEntry
from scripts.geopackage.extensions.vector_tiles.vector_fields.vector_fields_entry import VectorFieldsEntry
from scripts.geopackage.extensions.vector_tiles.vector_layers.vector_layers_entry import VectorLayersEntry
from sqlite3 import Cursor, Binary


class GeoPackageVectorTiles(Extension, GeoPackageAbstractTiles):
    """
    Abstract class representation of the GeoPackage Vector Tiles Extension.

    Represents the GeoPackage Vector Tiles extension. Defines the requirements for encoding the tile_data column
    in pyramid-user-data tables in a vector-tile format (rather than raster ie jpeg, png).  Also defines the
    relational tables needed for vector tiles on top of the gpkg_tile_matrix and gpkg_tile_matrix_set. Registers
    the extension in the GeoPackage Extensions table as well.
    """

    def __init__(self,
                 vector_tiles_table_name):
        super(GeoPackageVectorTiles, self).__init__(table_name=vector_tiles_table_name,
                                                    column_name="tile_data",
                                                    extension_name=self.extension_name,
                                                    # name depends if mapbox or geojson
                                                    definition=VECTOR_TILES_DEFINITION,
                                                    scope=EXTENSION_READ_WRITE_SCOPE)
        self.vector_tiles_table_name = vector_tiles_table_name

    @staticmethod
    def create_default_tiles_tables(cursor):
        """
        Creates the related tables required for storing tiles: gpkg_tile_matrix, gpkg_tile_matrix_set

        :param cursor: the cursor to the GeoPackage database's connection
        :type cursor: Cursor
        """
        # create the default tiles tables
        GeoPackageTiles.create_default_tiles_tables(cursor=cursor)
        GeoPackageVectorLayers.create_vector_layers_table(cursor=cursor)
        GeoPackageVectorFields.create_vector_fields_table(cursor=cursor)
        GeoPackageExtensions.insert_or_update_extensions_row(cursor=cursor,
                                                             extension=GeoPackageVectorFields())
        GeoPackageExtensions.insert_or_update_extensions_row(cursor=cursor,
                                                             extension=GeoPackageVectorLayers())

    def insert_or_update_vector_tiles_table(self,
                                            cursor,
                                            vector_tiles_content):
        """
        Adds all the default tables needed to add a vector-tiles table. It also registers the extension as well.

        :param cursor: the cursor to the GeoPackage database's connection
        :type cursor: Cursor

        :param vector_tiles_content: the vector tiles content information
        :type vector_tiles_content: VectorTilesContentEntry
        """
        GeoPackageVectorTiles.create_default_tiles_tables(cursor=cursor)
        # create the tiles table but with a vector-tiles data type
        GeoPackageTiles.create_pyramid_user_data_table(cursor=cursor,
                                                       tiles_content=vector_tiles_content)

        # register the extension
        # add the vector-tiles table extension
        GeoPackageExtensions.insert_or_update_extensions_row(cursor=cursor,
                                                             extension=self)

    def insert_or_update_tile_data(self,
                                   cursor,
                                   table_name,
                                   zoom_level,
                                   tile_column,
                                   tile_row,
                                   tile_data):
        """
        Inserts or updates row in the pyramid user data table with the table_name provided.

        :param cursor: the cursor to the GeoPackage database's connection
        :type cursor: Cursor

        :param table_name: Tile Pyramid User Data Table Name
        :type table_name: str

        :param zoom_level:  0 <= zoom_level <= max_level for table_name
        :type zoom_level: int

        :param tile_column:  0 to tile_matrix matrix_width - 1
        :type tile_column: int

        :param tile_row: 0 to tile_matrix matrix_height - 1
        :type tile_row: int

        :param tile_data: vector-tile encoded Binary data
        :type tile_data: Binary
        """
        self.insert_vector_layers_and_fields_from_tile_data(cursor=cursor, tile_data=tile_data, table_name=table_name)

        super(GeoPackageVectorTiles, self).insert_or_update_tile_data(cursor=cursor,
                                                                      table_name=table_name,
                                                                      zoom_level=zoom_level,
                                                                      tile_column=tile_column,
                                                                      tile_row=tile_row,
                                                                      tile_data=tile_data)

    @staticmethod
    @abstractmethod
    def insert_vector_layers_and_fields_from_tile_data(cursor,
                                                       tile_data,
                                                       table_name):
        # type: (Cursor, Binary, str) -> tuple[list[VectorLayersEntry], list[VectorFieldsEntry]]
        """
        Reads the tile_data and extracts the layers and fields information from the tile.

        :param cursor: the cursor to the GeoPackage database's connection
        :type cursor: Cursor

        :param tile_data: the tile_data
        :type tile_data: Binary

        :param table_name: the name of the table this tile_data belongs to
        :type table_name: str

        :returns: tuple where the first value is the list of VectorLayerEntry values and the second value is
        the list of VectorFieldsEntry values.
        :rtype: (list of VectorLayersEntry, list of VectorFieldsEntry)
        """
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def create_pyramid_user_data_table(cursor,
                                       tile_content):
        """
        Forces inherited classes to override this method when creating the tile-pyramid-user-data tables to also make
        sure the table is registered in the GeoPackage Extensions

        :param cursor:  the cursor to the GeoPackage database's connection
        :type cursor: Cursor

        :param tile_content:  The TileSet entry in the gpkg_contents table describing the vector-tiles in the GeoPackage
        :type tile_content: VectorTilesContentEntry
        """
        raise NotImplementedError()

    @abstractproperty
    def extension_name(self):
        """
        The Name of the Extension

        :return: the name of the extension
        :rtype: str
        """
        raise NotImplementedError
