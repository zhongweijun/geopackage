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
from scripts.geopackage.extensions.metadata.md_scope import MdScope
from scripts.geopackage.extensions.metadata.metadata import Metadata
from scripts.geopackage.extensions.metadata.metadata_reference.metadata_reference import MetadataReference
from scripts.geopackage.extensions.metadata.metadata_reference.reference_scope import ReferenceScope


class NsgMetadata(Metadata):

    def __init__(self,
                 metadata):
        super(NsgMetadata, self).__init__(md_scope=MdScope.SERIES,
                                          md_standard_uri='http://metadata.ces.mil/dse/ns/GSIP/nmis/2.2.0/doc',
                                          metadata=metadata)
        self.id = 1


class NsgMetadataReference(MetadataReference):

    def __init__(self):
        super(NsgMetadataReference, self).__init__(reference_scope=ReferenceScope.GEOPACKAGE,
                                                   table_name=None,
                                                   column_name=None,
                                                   row_identifier=None,
                                                   file_identifier=1,
                                                   parent_identifier=None)