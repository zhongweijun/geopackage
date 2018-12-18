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

from scripts.geopackage.extensions.extension import Extension, EXTENSION_WRITE_ONLY_SCOPE


# noinspection PyClassHasNoInit
class TestExtensions:

    def test_invalid_column_name(self):
        with raises(ValueError):
            Extension(table_name=None,
                      column_name="invalid",  # invalid
                      extension_name="name",
                      definition="definition",
                      scope=EXTENSION_WRITE_ONLY_SCOPE)

    def test_invalid_table_name(self):
        with raises(ValueError):
            Extension(table_name="",  # invalid
                      column_name=None,
                      extension_name="name",
                      definition="definition",
                      scope=EXTENSION_WRITE_ONLY_SCOPE)

    def test_invalid_column_name_2(self):
        with raises(ValueError):
            Extension(table_name="table",
                      column_name="",  # invalid
                      extension_name="name",
                      definition="definition",
                      scope=EXTENSION_WRITE_ONLY_SCOPE)

    def test_invalid_extension_name(self):
        with raises(ValueError):
            Extension(table_name="table",
                      column_name=None,
                      extension_name="",  # invalid
                      definition="definition",
                      scope=EXTENSION_WRITE_ONLY_SCOPE)

    def test_invalid_extension_name_2(self):
        with raises(ValueError):
            Extension(table_name="table",
                      column_name=None,
                      extension_name=None,  # invalid
                      definition="definition",
                      scope=EXTENSION_WRITE_ONLY_SCOPE)

    def test_invalid_scope(self):
        with raises(ValueError):
            Extension(table_name="table",
                      column_name=None,
                      extension_name="extension",
                      definition="definition",
                      scope="invalid")  # invalid

    def test_invalid_scope_2(self):
        with raises(ValueError):
            Extension(table_name="table",
                      column_name=None,
                      extension_name="extension",
                      definition="definition",
                      scope=None)  # invalid

    def test_invalid_definition(self):
        with raises(ValueError):
            Extension(table_name="table",
                      column_name=None,
                      extension_name="extension",
                      definition=None,  # invalid
                      scope=EXTENSION_WRITE_ONLY_SCOPE)
