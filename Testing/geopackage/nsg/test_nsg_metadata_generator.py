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

Authors:
    Steven D. Lander, Reinventing Geospatial Inc (RGi)
    Jenifer Cochran, Reinventing Geospatial Inc (RGi)
Date: 2018-11-11
   Requires: sqlite3, argparse
   Optional: Python Imaging Library (PIL or Pillow)
Credits:
  MapProxy imaging functions: http://mapproxy.org
  gdal2mb on github: https://github.com/developmentseed/gdal2mb

Version:
"""
from scripts.geopackage.core.geopackage_core import GeoPackageCore
from scripts.geopackage.tiles.geopackage_tiles import GeoPackageTiles
from Testing.test_tiles2gpkg import make_gpkg_nsg, make_zmd_list_geodetic, make_gpkg, DEFAULT_TILES_TABLE_NAME
from scripts.geopackage.extensions.metadata.geopackage_metadata import GeoPackageMetadata
from scripts.geopackage.nsg.nsg_metadata_generator import Generator, NameSpaces, Tags
from scripts.geopackage.utility.sql_utility import get_database_connection
from scripts.geopackage.nsg.nsg_metadata_generator import BoundingBox
from xml.etree.ElementTree import Element
from defusedxml import ElementTree as DET


class TestGenerator(object):

    def test_metadata_expected_values(self, make_gpkg_nsg):
        nsg_gpkg = make_gpkg_nsg
        nsg_gpkg.initialize()
        nsg_gpkg.update_metadata(make_zmd_list_geodetic())
        with get_database_connection(nsg_gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()

            all_metadata = GeoPackageMetadata.get_all_metadata(cursor=cursor)
            tile_matrix_set = GeoPackageTiles.get_tile_matrix_set_entry_by_table_name(cursor=cursor,
                                                                                      table_name=DEFAULT_TILES_TABLE_NAME)
            srs_entry = next((srs
                              for srs
                              in GeoPackageCore.get_all_spatial_reference_system_entries(cursor=cursor)
                              if srs.srs_id == tile_matrix_set.srs_id))
            expected_bounds = BoundingBox(min_x=tile_matrix_set.min_x,
                                          min_y=tile_matrix_set.min_y,
                                          max_x=tile_matrix_set.max_x,
                                          max_y=tile_matrix_set.max_y)

        assert len(all_metadata) == 1

        # get the xml and verify its contents
        metadata_xml = all_metadata[0].metadata

        TestGenerator.assert_metadata(metadata_xml=metadata_xml,
                                      expected_table_name=DEFAULT_TILES_TABLE_NAME,
                                      expected_abstract_message="Created by tiles2gpkg_parallel.py, written by S. Lander and J. Cochran",
                                      expected_organization="UNDEFINED",
                                      expected_bounds=expected_bounds,
                                      expected_srs_id=str(tile_matrix_set.srs_id),
                                      expected_srs_organization=srs_entry.organization)

    def test_metadata_expected_from_generator(self, make_gpkg):
        gpkg = make_gpkg
        gpkg.initialize()
        nsg_generator = Generator(gpkg.file_path)
        # create expected values
        expected_table_name = "table_test"  # type: str
        expected_abstract_message = "expected_abstract_message"
        expected_srs_id = "4326"
        expected_srs_organization = "epsg"
        expected_bounding_box = BoundingBox(1.0, 2.0, 3.4, 4.5)

        # add the identity to the metadata
        nsg_generator.add_layer_identity(layer_table_name=expected_table_name,
                                         abstract_msg=expected_abstract_message,
                                         BBOX=expected_bounding_box,
                                         srs_id=str(expected_srs_id),
                                         srs_organization=expected_srs_organization)
        nsg_generator.write_metadata()

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()

            all_metadata = GeoPackageMetadata.get_all_metadata(cursor=cursor)

            # get the xml and verify its contents
            metadata_xml = all_metadata[0].metadata

            TestGenerator.assert_metadata(metadata_xml=metadata_xml,
                                          expected_table_name=expected_table_name,
                                          expected_abstract_message=expected_abstract_message,
                                          expected_organization="UNDEFINED",
                                          expected_bounds=expected_bounding_box,
                                          expected_srs_id=str(expected_srs_id),
                                          expected_srs_organization=expected_srs_organization)

    def test_adding_same_metadata_twice(self, make_gpkg):
        gpkg = make_gpkg
        gpkg.initialize()
        nsg_generator = Generator(gpkg.file_path)
        # create expected values
        expected_table_name = "table_test"
        expected_abstract_message = "expected_abstract_message"
        expected_srs_id = "432612312312"
        expected_srs_organization = "epsgasdfasdfs"
        expected_bounding_box = BoundingBox(1.0, 2.0, 3.4, 4.5)

        # add the identity to the metadata
        nsg_generator.add_layer_identity(layer_table_name=expected_table_name,
                                         abstract_msg=expected_abstract_message,
                                         BBOX=expected_bounding_box,
                                         srs_id=expected_srs_id,
                                         srs_organization=expected_srs_organization)
        nsg_generator.write_metadata()

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()

            all_metadata = GeoPackageMetadata.get_all_metadata(cursor=cursor)

        # get the xml and verify its contents
        metadata_xml = all_metadata[0].metadata

        TestGenerator.assert_metadata(metadata_xml=metadata_xml,
                                      expected_table_name=expected_table_name,
                                      expected_abstract_message=expected_abstract_message,
                                      expected_organization="UNDEFINED",
                                      expected_bounds=expected_bounding_box,
                                      expected_srs_id=str(expected_srs_id),
                                      expected_srs_organization=expected_srs_organization)

        # add the SAME identity to the metadata
        nsg_generator.add_layer_identity(layer_table_name=expected_table_name,
                                         abstract_msg=expected_abstract_message,
                                         BBOX=expected_bounding_box,
                                         srs_id=str(expected_srs_id),
                                         srs_organization=expected_srs_organization)

        nsg_generator.write_metadata()

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()

            all_metadata = GeoPackageMetadata.get_all_metadata(cursor=cursor)

            # get the xml and verify its contents
            metadata_xml_again = all_metadata[0].metadata
            TestGenerator.assert_metadata(metadata_xml=metadata_xml,
                                          expected_table_name=expected_table_name,
                                          expected_abstract_message=expected_abstract_message,
                                          expected_organization="UNDEFINED",
                                          expected_bounds=expected_bounding_box,
                                          expected_srs_id=str(expected_srs_id),
                                          expected_srs_organization=expected_srs_organization)

    @staticmethod
    def assert_metadata(metadata_xml,
                        expected_table_name,
                        expected_abstract_message,
                        expected_organization,
                        expected_bounds,
                        expected_srs_id,
                        expected_srs_organization):
        """
        Asserts that the metadata xml contains the values it should for a particular tiles table
        
        :param expected_srs_id: the expected srs_id that should be in the metadata xml
        :type expected_srs_id: str
        :param expected_srs_organization: the expected srs organization that should be in the xml
        :type expected_srs_organization: str
        :param metadata_xml: the actual xml generated
        :type metadata_xml: str
        :param expected_table_name: the name of the tiles table that should be in the xml
        :type expected_table_name: str
        :param expected_abstract_message: the expected abstract message in the xml
        :type expected_abstract_message: str
        :param expected_organization: the expected organization name in the xml
        :type expected_organization: str
        :param expected_bounds: the expected bounds of the tiles data in the xml
        :type expected_bounds: BoundingBox
        """
        tree = DET.fromstring(metadata_xml)
        md_identification = Generator.find_table_identity(base=tree,
                                                          table_name=expected_table_name)
        assert md_identification is not None
        TestGenerator.assert_spatial_reference_system(expected_srs_id=expected_srs_id,
                                                      expected_srs_organization=expected_srs_organization,
                                                      root=tree)
        # check CI Citation (title and date)
        TestGenerator.assert_ci_citation(title_expected=expected_table_name,
                                         md_identification=md_identification)
        # check Abstract (abstract message)
        TestGenerator.assert_abstract(abstract_message_expected=expected_abstract_message,
                                      md_identification=md_identification)
        # Check organization (organization name)
        TestGenerator.assert_organization(organization_name_expected=expected_organization,
                                          md_identification=md_identification)
        # check extent
        bounding_box = Generator.find_bounding_box_tag(data_identification_element=md_identification)
        TestGenerator.assert_bounds(expected_bounds=expected_bounds,
                                    bounding_box_tag=bounding_box)

    @staticmethod
    def assert_spatial_reference_system(expected_srs_id, expected_srs_organization, root):
        """
        Asserts if the srs is in the xml or not
        :param expected_srs_id: the expected srs_id value to be in the xml
        :type expected_srs_id: str
        :param expected_srs_organization: the expected srs_organization to be in the xml
        :type expected_srs_organization: str
        :param root: the root of the xml
        :type root: Element
        """
        existing_spatial_ref_systems = Generator.find_all_spatial_reference_system_ri_identifier_tags(root=root)

        for srs in existing_spatial_ref_systems:
            org = Generator.find_code_space_from_ri_identifier_tag(srs).text
            code = Generator.find_code_from_ri_identifer_tag(srs).text
            if expected_srs_id == code and expected_srs_organization == org:
                return

        # no matching srs entries in the xml
        assert False

    @staticmethod
    def assert_organization(organization_name_expected, md_identification):
        organization = Generator.find_organization_element(md_identification)
        org_name = organization.find("{gco}:{char_string}".format(gco=NameSpaces.GCO.value[0],
                                                                  char_string=Tags.CHAR_STRING),
                                     Generator.generate_namespace_map())
        assert org_name.text == organization_name_expected

    @staticmethod
    def assert_ci_citation(title_expected, md_identification):
        # check CI Citation (title and date)
        ci_citation = Generator.find_ci_citation(md_identification)
        # title should match the name of the table
        title = ci_citation.find("{gmd}:title/{gco}:{char_str}".format(gmd=NameSpaces.GMD.value[0],
                                                                       gco=NameSpaces.GCO.value[0],
                                                                       char_str=Tags.CHAR_STRING),
                                 Generator.generate_namespace_map())
        assert title.text == title_expected

    @staticmethod
    def assert_abstract(abstract_message_expected, md_identification):
        abstract = Generator.find_abstract_element(md_identification)
        message = abstract.find("{gco}:{char_string}".format(gco=NameSpaces.GCO.value[0],
                                                             char_string=Tags.CHAR_STRING),
                                Generator.generate_namespace_map())
        assert message.text == abstract_message_expected

    @staticmethod
    def assert_bounds(expected_bounds, bounding_box_tag):
        """

        :param expected_bounds: the bounds that is expected to be in the metadata
        :type expected_bounds: BoundingBox
        :param bounding_box_tag: the bounding box element tag to see if the bounds were correctly set
        :type bounding_box_tag: Element
        """

        # north
        north = bounding_box_tag.find(".//{tag}:{name}/{tag2}:{decimal}".format(tag=NameSpaces.GMD.value[0],
                                                                                name=Tags.Extent.N_BOUND_LAT,
                                                                                tag2=NameSpaces.GCO.value[0],
                                                                                decimal=Tags.Extent.DECIMAL),
                                      Generator.generate_namespace_map())
        assert north.text == str(expected_bounds.max_y)
        # south
        south = bounding_box_tag.find(
            ".//{tag}:{name}/{tag2}:{decimal}".format(tag=NameSpaces.GMD.value[0],
                                                      name=Tags.Extent.S_BOUND_LAT,
                                                      tag2=NameSpaces.GCO.value[0],
                                                      decimal=Tags.Extent.DECIMAL),
            Generator.generate_namespace_map())
        assert south.text == str(expected_bounds.min_y)
        # east
        east = bounding_box_tag.find(
            ".//{tag}:{name}/{tag2}:{decimal}".format(tag=NameSpaces.GMD.value[0],
                                                      name=Tags.Extent.E_BOUND_LON,
                                                      tag2=NameSpaces.GCO.value[0],
                                                      decimal=Tags.Extent.DECIMAL),
            Generator.generate_namespace_map())
        assert east.text == str(expected_bounds.max_x)
        # west
        west = bounding_box_tag.find(
            ".//{tag}:{name}/{tag2}:{decimal}".format(tag=NameSpaces.GMD.value[0],
                                                      name=Tags.Extent.W_BOUND_LON,
                                                      tag2=NameSpaces.GCO.value[0],
                                                      decimal=Tags.Extent.DECIMAL),
            Generator.generate_namespace_map())
        assert west.text == str(expected_bounds.min_x)
