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

from scripts.geopackage.extensions.vector_tiles.vector_fields.vector_fields_entry import VectorFieldType


class TestVectorFieldsEntry(object):

    def test_get_vector_field_type_from_text_boolean(self):
        assert VectorFieldType.get_vector_field_type_from_text("Boolean") == VectorFieldType.BOOLEAN

    def test_get_vector_field_type_from_text_string(self):
        assert VectorFieldType.get_vector_field_type_from_text("strInG") == VectorFieldType.STRING

    def test_get_vector_field_type_from_text_number(self):
        assert VectorFieldType.get_vector_field_type_from_text("NuMbER") == VectorFieldType.NUMBER

    def test_get_vector_field_type_from_text_error(self):
        with raises(ValueError):
            VectorFieldType.get_vector_field_type_from_text("DoeSnTWoRk")

    def test_convert_string_value_to_vector_field_type_integer(self):
        assert VectorFieldType.NUMBER == VectorFieldType.convert_string_value_to_vector_field_type('10000')

    def test_convert_string_value_to_vector_field_type_float(self):
        assert VectorFieldType.NUMBER == VectorFieldType.convert_string_value_to_vector_field_type('110.002')

    def test_convert_string_value_to_vector_field_type_boolean(self):
        assert VectorFieldType.BOOLEAN == VectorFieldType.convert_string_value_to_vector_field_type('True')

    def test_convert_string_value_to_vector_field_type_boolean_2(self):
        assert VectorFieldType.BOOLEAN == VectorFieldType.convert_string_value_to_vector_field_type('False')

    def test_convert_string_value_to_vector_field_type_string(self):
        assert VectorFieldType.STRING == VectorFieldType.convert_string_value_to_vector_field_type('1.0 value')

    def test_convert_string_value_to_vector_field_type_string_with_trailing_spaces(self):
        assert VectorFieldType.STRING == VectorFieldType.convert_string_value_to_vector_field_type('1.0 string  ')

