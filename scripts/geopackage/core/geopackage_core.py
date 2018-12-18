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

from sqlite3 import Cursor

import typing

from scripts.geopackage.core.content_entry import ContentEntry
from scripts.geopackage.core.spatial_ref_system_entry import SpatialReferenceSystemEntry
from scripts.geopackage.srs.geodetic_nsg import GeodeticNSG
from scripts.geopackage.srs.undefined_cartesian_coord_ref_sys import UndefinedCartesianCoordinateReferenceSystem
from scripts.geopackage.srs.undefined_geographic_coord_ref_sys import UndefinedGeographicCoordinateReferenceSystem
from scripts.geopackage.utility.sql_utility import table_exists

GEOPACKAGE_SPATIAL_REFERENCE_SYSTEM_TABLE_NAME = 'gpkg_spatial_ref_sys'
GEOPACKAGE_CONTENTS_TABLE_NAME = 'gpkg_contents'


class GeoPackageCore(object):
    """
    'Core' subsystem of the GeoPackage implementation.  Responsible for the gpkg_contents and
    gpkg_spatial_ref_sys tables.
    """

    @staticmethod
    def create_spatial_reference_table(cursor):
        """
         Creates the gpkg_spatial_ref_sys table

        :param cursor: the cursor to the GeoPackage database's connection
        :type cursor: Cursor
        """
        cursor.execute("""
                        CREATE TABLE IF NOT EXISTS {table_name} (
                            srs_name TEXT NOT NULL,
                            srs_id INTEGER NOT NULL PRIMARY KEY,
                            organization TEXT NOT NULL,
                            organization_coordsys_id INTEGER NOT NULL,
                            definition TEXT NOT NULL,
                            description TEXT);
                        """.format(table_name=GEOPACKAGE_SPATIAL_REFERENCE_SYSTEM_TABLE_NAME))

    @staticmethod
    def add_default_spatial_reference_systems(cursor):
        """
        Adds the default Spatial Reference Systems that must be part of every GeoPackage. According to
        requirement 11. See: http://www.geopackage.org/spec121/#gpkg_spatial_ref_sys_records

        :param cursor: the cursor to the GeoPackage database's connection
        :type cursor: Cursor
        """
        # Insert EPSG values for tiles table
        geodetic = GeodeticNSG()
        undefined_cartesian = UndefinedCartesianCoordinateReferenceSystem()
        undefined_geographic = UndefinedGeographicCoordinateReferenceSystem()
        GeoPackageCore.insert_spatial_reference_system_row(cursor,
                                                           geodetic)
        GeoPackageCore.insert_spatial_reference_system_row(cursor,
                                                           undefined_cartesian)
        GeoPackageCore.insert_spatial_reference_system_row(cursor,
                                                           undefined_geographic)

    @staticmethod
    def insert_spatial_reference_system_row(cursor,
                                            spatial_reference_system):
        """
        Adds or updates the spatial reference system to the gpkg_spatial_ref_sys table.
        
        :param cursor: the cursor to the GeoPackage database's connection
        :type cursor: Cursor

        :param spatial_reference_system: The spatial reference system to add to the GeoPackage gpkg_spatial_ref_sys
        table
        :type spatial_reference_system: SpatialReferenceSystemEntry
        """
        if not table_exists(cursor, GEOPACKAGE_SPATIAL_REFERENCE_SYSTEM_TABLE_NAME):
            raise ValueError("Cannot add row to {table} because it does not exist"
                             .format(table=GEOPACKAGE_SPATIAL_REFERENCE_SYSTEM_TABLE_NAME))
        GeoPackageCore.__insert_spatial_reference_system_row(cursor=cursor,
                                                             srs_id=spatial_reference_system.srs_id,
                                                             organization=spatial_reference_system.organization,
                                                             organization_coordsys_id=spatial_reference_system.organization_coordsys_id,
                                                             srs_name=spatial_reference_system.srs_name,
                                                             definition=spatial_reference_system.definition,
                                                             description=spatial_reference_system.description)

    @staticmethod
    def __insert_spatial_reference_system_row(cursor,
                                              srs_id,
                                              organization,
                                              organization_coordsys_id,
                                              srs_name,
                                              definition,
                                              description):
        """
         Inserts or replaces the spatial reference system entry in the gpkg_spatial_ref_sys table

        :param cursor: the cursor to the GeoPackage database's connection
        :type cursor: Cursor

        :param srs_id: Unique identifier for each Spatial Reference System within a GeoPackage
        :type srs_id: int

        :param organization: Case-insensitive name of the defining organization e.g. EPSG or epsg
        :type organization: str

        :param organization_coordsys_id: Numeric ID of the Spatial Reference System assigned by the organization
        :type organization_coordsys_id: int

        :param srs_name: Human readable name of this SRS
        :type srs_name: str

        :param definition: Well-known Text Representation of the Spatial Reference System.
        see http://www.geopackage.org/spec121/#A32
        :type definition: str

        :param description: Human readable description of this SRS
        :type description: str
        """

        cursor.execute("""
                           INSERT OR REPLACE INTO {table_name} 
                              (srs_id,
                               organization,
                               organization_coordsys_id,
                               srs_name,
                               definition,
                               description)
                           VALUES (?, ?, ?, ?, ?, ?)
                       """.format(table_name=GEOPACKAGE_SPATIAL_REFERENCE_SYSTEM_TABLE_NAME),
                       (srs_id,
                        organization,
                        organization_coordsys_id,
                        srs_name,
                        definition,
                        description,))

    @staticmethod
    def insert_or_update_content(cursor,
                                 content):
        """
         Adds a row to the GeoPackage Content's table gpkg_contents. To describe the geospatial content that is contained
        in this GeoPackage

        :param cursor: the cursor to the GeoPackage database's connection
        :type cursor: Cursor

        :param content: the content to add to the GeoPackage
        :type content: ContentEntry
        """
        GeoPackageCore.insert_or_update_contents_row(cursor=cursor,
                                                     table_name=content.table_name,
                                                     data_type=content.data_type,
                                                     identifier=content.identifier,
                                                     min_x=content.min_x,
                                                     min_y=content.min_y,
                                                     max_x=content.max_x,
                                                     max_y=content.max_y,
                                                     srs_id=content.srs_id)

    @staticmethod
    def insert_or_update_contents_row(cursor,
                                      table_name,
                                      data_type,
                                      identifier,
                                      min_x,
                                      min_y,
                                      max_x,
                                      max_y,
                                      srs_id):
        """
        Adds a row to the GeoPackage Content's table gpkg_contents. To describe the geospatial content that is contained
        in this GeoPackage

        :param cursor: the cursor to the GeoPackage database's connection
        :type cursor: Cursor

        :param table_name: The name of the actual content (e.g., tiles, features, or attributes) table
        :type table_name: str

        :param data_type: Type of data stored in the table
        :type data_type: str

        :param identifier: A human-readable identifier (e.g. short name) for the table_name content
        :type identifier: str

        :param min_x: Bounding box minimum easting or longitude for all content in table_name.
        If tiles, this is informational and the tile matrix set should be used for calculating tile coordinates.
        :type min_x: float

        :param min_y: Bounding box minimum northing or latitude for all content in table_name.
        If tiles, this is informational and the tile matrix set should be used for calculating tile coordinates.
        :type min_y: float

        :param max_x: Bounding box maximum easting or longitude for all content in table_name.
         If tiles, this is informational and the tile matrix set should be used for calculating tile coordinates.
        :type max_x: float

        :param max_y: Bounding box maximum northing or latitude for all content in table_name.
         If tiles, this is informational and the tile matrix set should be used for calculating tile coordinates.
        :type max_y: float

        :param srs_id: Spatial Reference System ID: gpkg_spatial_ref_sys.srs_id; when data_type is features,
        SHALL also match gpkg_geometry_columns.srs_id; When data_type is tiles, SHALL also match
        gpkg_tile_matrix_set.srs_id
        :type srs_id: int
        """
        if not table_exists(cursor, GEOPACKAGE_CONTENTS_TABLE_NAME):
            GeoPackageCore.create_core_tables(cursor=cursor)

        cursor.execute("""
                           INSERT OR REPLACE INTO {table_name} 
                              (table_name,
                               data_type,
                               identifier,
                               description,
                               min_x,
                               max_x,
                               min_y,
                               max_y,
                               srs_id)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                       """.format(table_name=GEOPACKAGE_CONTENTS_TABLE_NAME),
                       (table_name,
                        data_type,
                        identifier,
                        "Created by tiles2gpkg_parallel.py, written by S. Lander and J. Cochran",
                        min_x,
                        max_x,
                        min_y,
                        max_y,
                        srs_id))

    @staticmethod
    def create_geopackage_contents_table(cursor):
        """
        Creates the GeoPackage contents table gpkg_contents. The gpkg_contents table is intended to provide a list of
         all geospatial contents in a GeoPackage. It provides identifying and descriptive information that an
         application can display to a user as a menu of geospatial data that is available for access and/or update.

        :param cursor: the cursor to the GeoPackage database's connection
        :type cursor: Cursor
        """
        cursor.execute("""
                         CREATE TABLE IF NOT EXISTS {table_name}
                         (table_name  TEXT     NOT NULL PRIMARY KEY,                                    -- The name of the tiles, or feature table
                          data_type   TEXT     NOT NULL,                                                -- Type of data stored in the table: "features" per clause Features (http://www.geopackage.org/spec/#features), "tiles" per clause Tiles (http://www.geopackage.org/spec/#tiles), or an implementer-defined value for other data tables per clause in an Extended GeoPackage
                          identifier  TEXT     UNIQUE,                                                  -- A human-readable identifier (e.g. short name) for the table_name content
                          description TEXT     DEFAULT '',                                              -- A human-readable description for the table_name content
                          last_change DATETIME NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')), -- Timestamp value in ISO 8601 format as defined by the strftime function %Y-%m-%dT%H:%M:%fZ format string applied to the current time
                          min_x       DOUBLE,                                                           -- Bounding box minimum easting or longitude for all content in table_name
                          min_y       DOUBLE,                                                           -- Bounding box minimum northing or latitude for all content in table_name
                          max_x       DOUBLE,                                                           -- Bounding box maximum easting or longitude for all content in table_name
                          max_y       DOUBLE,                                                           -- Bounding box maximum northing or latitude for all content in table_name
                          srs_id      INTEGER,                                                          -- Spatial Reference System ID: gpkg_spatial_ref_sys.srs_id; when data_type is features, SHALL also match gpkg_geometry_columns.srs_id; When data_type is tiles, SHALL also match gpkg_tile_matrix_set.srs.id
                          CONSTRAINT fk_gc_r_srs_id FOREIGN KEY (srs_id) REFERENCES gpkg_spatial_ref_sys(srs_id))
                       """.format(table_name=GEOPACKAGE_CONTENTS_TABLE_NAME))

    @staticmethod
    def create_core_tables(cursor):
        """
        Creates the GeoPackage Contents table and the GeoPackage Spatial Reference Table with the default populated
        values that are required to be a valid GeoPackage.

        :param cursor: the cursor to the GeoPackage database's connection
        :type cursor: Cursor
        """
        GeoPackageCore.create_geopackage_contents_table(cursor)
        GeoPackageCore.create_spatial_reference_table(cursor)
        GeoPackageCore.add_default_spatial_reference_systems(cursor)

    @staticmethod
    def get_all_content_entries(cursor):
        """
        Returns all the content entries in the GeoPackage Contents table (gpkg_contents)

        :param cursor: the cursor to the GeoPackage database's connection
        :type cursor: Cursor

        :return Returns all the content entries in the GeoPackage Contents table (gpkg_contents)
        :rtype: list of Content
        """
        if not table_exists(cursor, GEOPACKAGE_CONTENTS_TABLE_NAME):
            return []

        # select all the rows
        cursor.execute("SELECT * FROM {table_name};".format(table_name=GEOPACKAGE_CONTENTS_TABLE_NAME))

        rows = cursor.fetchall()

        if rows is None:
            return []

        return [ContentEntry(table_name=row['table_name'],
                             data_type=row['data_type'],
                             identifier=row['identifier'],
                             min_x=row['min_x'],
                             min_y=row['min_y'],
                             max_x=row['max_x'],
                             max_y=row['max_y'],
                             srs_id=row['srs_id']) for row in rows]

    @staticmethod
    def get_content_entry_by_table_name(cursor, table_name):
        # type: (Cursor, str) -> typing.Union[ContentEntry, None]
        """
        Returns the content entry in the GeoPackage Contents table (gpkg_contents) where the table_name column
        matches the table_name passed in or None if none match

        :param table_name: the name of the table that is being searched for
        :type table_name: str

        :param cursor: the cursor to the GeoPackage database's connection
        :type cursor: Cursor

        :return Returns the content entry in the GeoPackage Contents table (gpkg_contents) where the table_name column
        matches the table_name passed in or None if none match
        :rtype: ContentEntry, None
        """
        if not table_exists(cursor, GEOPACKAGE_CONTENTS_TABLE_NAME):
            return None
        # select all the rows
        cursor.execute("SELECT * FROM {table_name} WHERE table_name = ?;"
                       .format(table_name=GEOPACKAGE_CONTENTS_TABLE_NAME),
                       (table_name,))

        row = cursor.fetchone()
        # no matches found
        if row is None:
            return None

        return ContentEntry(table_name=row['table_name'],
                            data_type=row['data_type'],
                            identifier=row['identifier'],
                            min_x=row['min_x'],
                            min_y=row['min_y'],
                            max_x=row['max_x'],
                            max_y=row['max_y'],
                            srs_id=row['srs_id'])

    @staticmethod
    def get_all_spatial_reference_system_entries(cursor):
        """
        Returns all the spatial reference system entries in the GeoPackage Spatial Reference System table
        (gpkg_spatial_ref_sys)

        :param cursor: the cursor to the GeoPackage database's connection
        :type cursor: Cursor

        :return Returns all the spatial reference system entries in the GeoPackage Spatial Reference System table
        (gpkg_spatial_ref_sys)
        :rtype: list of SpatialReferenceSystemEntry
        """
        if not table_exists(cursor, GEOPACKAGE_CONTENTS_TABLE_NAME):
            return []

        # select all the rows
        cursor.execute("SELECT * FROM {table_name};".format(table_name=GEOPACKAGE_SPATIAL_REFERENCE_SYSTEM_TABLE_NAME))

        return [SpatialReferenceSystemEntry(srs_name=row['srs_name'],
                                            srs_id=row['srs_id'],
                                            organization=row['organization'],
                                            organization_coordsys_id=row['organization_coordsys_id'],
                                            definition=row['definition'],
                                            description=row['description']) for row in cursor]
