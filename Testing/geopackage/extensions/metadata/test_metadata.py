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

from scripts.geopackage.extensions.metadata.md_scope import MdScope
from scripts.geopackage.extensions.metadata.metadata import Metadata


class TestMetadata(object):

    def test_invalid_metadata_uri(self):
        with raises(ValueError):
            Metadata(md_scope=MdScope.SERIES,
                     md_standard_uri=None,  # invalid
                     mime_type='text/xml',
                     metadata="metadata")

    def test_invalid_metadata_scope(self):
        with raises(ValueError):
            fake_scope = namedtuple('MdScope', 'value')
            fake_scope.value = "NotReal"
            Metadata(md_scope=fake_scope,  # invalid
                     md_standard_uri='http://metadata.ces.mil/dse/ns/GSIP/nmis/2.2.0/doc',
                     mime_type='text/xml',
                     metadata="metadata")

    def test_invalid_mime_type(self):
        with raises(ValueError):
            Metadata(md_scope=MdScope.SERIES,
                     md_standard_uri='http://metadata.ces.mil/dse/ns/GSIP/nmis/2.2.0/doc',
                     mime_type='text/xmlNOPE',  # invalid
                     metadata="metadata")


    def test_invalid_metadata(self):
        with raises(ValueError):
            Metadata(md_scope=MdScope.SERIES,
                     md_standard_uri='http://metadata.ces.mil/dse/ns/GSIP/nmis/2.2.0/doc',
                     mime_type='text/xml',
                     metadata=None)  # invalid

