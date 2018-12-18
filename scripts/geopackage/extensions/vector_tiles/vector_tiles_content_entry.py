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

from scripts.geopackage.tiles.tiles_content_entry import TilesContentEntry


class VectorTilesContentEntry(TilesContentEntry):
    """
    Represents a vector-tile in the gpkg_contents table
    """

    def __init__(self,
                 table_name,
                 identifier,
                 min_x,
                 min_y,
                 max_x,
                 max_y,
                 srs_id):
        """
        Constructor

        :param table_name: the name of the vector-tiles table
        :type table_name: str

        :param identifier: A human-readable identifier (e.g. short name) for the table_name content
        :type identifier: str

        :param min_x: Bounding box minimum easting or longitude for all content in table_name. If tiles, this is
        informational and the tile matrix set should be used for calculating tile coordinates.
        :type min_x: float

        :param min_y: Bounding box maximum easting or longitude for all content in table_name. If tiles, this is
        informational and the tile matrix set should be used for calculating tile coordinates.
        :type min_y: float

        :param max_x: Bounding box minimum northing or latitude for all content in table_name. If tiles, this is
        informational and the tile matrix set should be used for calculating tile coordinates.
        :type max_x: float

        :param max_y: Bounding box maximum northing or latitude for all content in table_name. If tiles, this is
        informational and the tile matrix set should be used for calculating tile coordinates.
        :type max_y: float

        :param srs_id: Spatial Reference System ID: gpkg_spatial_ref_sys.srs_id; When data_type is tiles,
        SHALL also match gpkg_tile_matrix_set.srs_id
        :type srs_id: int
        """
        super(VectorTilesContentEntry, self).__init__(table_name=table_name,
                                                      identifier=identifier,
                                                      min_x=min_x,
                                                      min_y=min_y,
                                                      max_x=max_x,
                                                      max_y=max_y,
                                                      srs_id=srs_id)

    data_type = "vector_tiles"
