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
from collections import namedtuple

from pytest import raises

from scripts.geopackage.extensions.metadata.metadata_reference.metadata_reference import MetadataReference
from scripts.geopackage.extensions.metadata.metadata_reference.reference_scope import ReferenceScope


class TestMetadataReference(object):

    def test_invalid_reference_scope_none(self):
        with raises(ValueError):
            MetadataReference(reference_scope=None,  # invalid
                              table_name='TableName',
                              column_name='columnName',
                              row_identifier=0,
                              file_identifier=1,
                              parent_identifier=2)

    def test_invalid_reference_scope_value(self):
        fake_scope = namedtuple('ReferenceScope', 'value')
        fake_scope.value = 'NotReal'
        with raises(ValueError):
            MetadataReference(reference_scope=fake_scope,  # invalid
                              table_name='TableName',
                              column_name='columnName',
                              row_identifier=0,
                              file_identifier=1,
                              parent_identifier=2)

    def test_invalid_reference_scope_gpkg_table_combo(self):
        with raises(ValueError):
            MetadataReference(reference_scope=ReferenceScope.GEOPACKAGE,  # invalid combo
                              table_name='TableName',  # invalid combo
                              column_name=None,
                              row_identifier=0,
                              file_identifier=1,
                              parent_identifier=2)

    def test_invalid_reference_scope_column_scope(self):
        with raises(ValueError):
            MetadataReference(reference_scope=ReferenceScope.GEOPACKAGE,  # invalid combo
                              table_name=None,
                              column_name='columnName',  # invalid combo
                              row_identifier=0,
                              file_identifier=1,
                              parent_identifier=2)

    def test_invalid_reference_scope_row_scope(self):
        with raises(ValueError):
            MetadataReference(reference_scope=ReferenceScope.ROW_COL,  # invalid combo
                              table_name=None,
                              column_name='columnName',
                              row_identifier=None,  # invalid combo
                              file_identifier=1,
                              parent_identifier=2)

    def test_invalid_reference_table_name(self):
        with raises(ValueError):
            MetadataReference(reference_scope=ReferenceScope.ROW_COL,
                              table_name='',  # invalid
                              column_name='columnName',
                              row_identifier=0,
                              file_identifier=1,
                              parent_identifier=2)

    def test_invalid_reference_column_name(self):
        with raises(ValueError):
            MetadataReference(reference_scope=ReferenceScope.ROW_COL,
                              table_name='TableName',
                              column_name='',  # invalid
                              row_identifier=0,
                              file_identifier=1,
                              parent_identifier=2)

    def test_invalid_reference_file_identifier(self):
        with raises(ValueError):
            MetadataReference(reference_scope=ReferenceScope.ROW_COL,
                              table_name='TableName',
                              column_name='ColumnName',
                              row_identifier=0,
                              file_identifier=None,  # invalid
                              parent_identifier=2)
