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

from scripts.geopackage.extensions.extension import Extension, EXTENSION_READ_WRITE_SCOPE
from scripts.geopackage.extensions.geopackage_extensions import GeoPackageExtensions
from scripts.geopackage.extensions.metadata.md_scope import MdScope
from scripts.geopackage.extensions.metadata.metadata import Metadata
from scripts.geopackage.extensions.metadata.metadata_reference.geopackage_metadata_reference import \
    GEOPACKAGE_METADATA_EXTENSION_NAME, GEOPACKAGE_METADATA_EXTENSION_DEFINITION
from sqlite3 import Cursor

from scripts.geopackage.utility.sql_utility import table_exists

GEOPACKAGE_METADATA_TABLE_NAME = "gpkg_metadata"


class GeoPackageMetadata(Extension):
    """
    GeoPackage Metadata Subsystem extension representation
    """

    def __init__(self):
        super(GeoPackageMetadata, self).__init__(table_name=GEOPACKAGE_METADATA_TABLE_NAME,
                                                 column_name=None,
                                                 scope=EXTENSION_READ_WRITE_SCOPE,
                                                 definition=GEOPACKAGE_METADATA_EXTENSION_DEFINITION,
                                                 extension_name=GEOPACKAGE_METADATA_EXTENSION_NAME)

    @staticmethod
    def create_metadata_table(cursor):
        """
        Creates the gpkg_metadata table and registers the table as an extension to the GeoPackage
        see http://www.geopackage.org/spec121/#metadata_table_table_definition

        :param cursor: the cursor to the GeoPackage database's connection
        :type cursor: Cursor
        """
        # create the metadata table
        cursor.execute("""
                         CREATE TABLE IF NOT EXISTS {table_name}
                         (id              INTEGER CONSTRAINT m_pk PRIMARY KEY ASC NOT NULL UNIQUE,             -- Metadata primary key
                          md_scope        TEXT                                    NOT NULL DEFAULT 'dataset',  -- Case sensitive name of the data scope to which this metadata applies; see Metadata Scopes
                          md_standard_uri TEXT                                    NOT NULL,                    -- URI reference to the metadata structure definition authority
                          mime_type       TEXT                                    NOT NULL DEFAULT 'text/xml', -- MIME encoding of metadata
                          metadata        TEXT                                    NOT NULL DEFAULT ''          -- metadata
                         );
                       """.format(table_name=GEOPACKAGE_METADATA_TABLE_NAME))

        # register extension in the extensions table
        if GEOPACKAGE_METADATA_TABLE_NAME not in \
                [extension.table_name for extension in GeoPackageExtensions.get_all_extensions(cursor=cursor)]:
            GeoPackageExtensions.insert_or_update_extensions_row(cursor=cursor, extension=GeoPackageMetadata())

    @staticmethod
    def insert_or_update_metadata_row(cursor,
                                      metadata):
        """
        Inserts or updates the metadata entry into gpkg_metadata table.

        :param cursor: the cursor to the GeoPackage database's connection
        :type cursor: Cursor

        :param metadata:  The Metadata entry to insert into the gpkg_metadata table
        :type metadata: Metadata
        """

        if not table_exists(cursor=cursor, table_name=GEOPACKAGE_METADATA_TABLE_NAME):
            GeoPackageMetadata.create_metadata_table(cursor=cursor)

        cursor.execute("""
                          INSERT OR REPLACE INTO {table_name} (md_scope,
                                                               md_standard_uri,
                                                               mime_type,
                                                               metadata)
                          VALUES (?, ?, ?, ?);
                       """.format(table_name=GEOPACKAGE_METADATA_TABLE_NAME), (metadata.md_scope.value,
                                                                               metadata.md_standard_uri,
                                                                               metadata.mime_type,
                                                                               metadata.metadata))

    @staticmethod
    def get_all_metadata(cursor):
        """
        Returns all the rows in the gpkg_metadata table

        :param cursor: the cursor to the GeoPackage database's connection
        :type cursor: Cursor

        :return all the rows in the gpkg_metadata table
        :rtype: list of Metadata
        """
        if not table_exists(cursor=cursor, table_name=GEOPACKAGE_METADATA_TABLE_NAME):
            return []

        # select all the rows
        cursor.execute("SELECT * FROM {table_name};".format(table_name=GEOPACKAGE_METADATA_TABLE_NAME))

        # get the results
        return [Metadata(md_scope=MdScope.from_text(row['md_scope']),
                         md_standard_uri=row['md_standard_uri'],
                         mime_type=row['mime_type'],
                         metadata=row['metadata']) for row in cursor]
