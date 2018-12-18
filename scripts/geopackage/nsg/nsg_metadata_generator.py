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
import datetime
import os
import sqlite3
from os.path import join
from xml.etree.ElementTree import QName, Element, SubElement, register_namespace, tostring

from defusedxml import ElementTree as DET
from enum import Enum

from scripts.geopackage.extensions.metadata.geopackage_metadata import GeoPackageMetadata
from scripts.geopackage.extensions.metadata.metadata_reference.geopackage_metadata_reference import \
    GeoPackageMetadataReference
from scripts.geopackage.extensions.metadata.metadata import Metadata
from scripts.geopackage.nsg.nsg_metadata import NsgMetadata, NsgMetadataReference
from scripts.geopackage.utility.sql_utility import get_database_connection


class NameSpaces(Enum):
    """
    Namespaces used to create NSG Metadata.
    """

    NAS = ("nas", "http://metadata.ces.mil/dse/ns/GSIP/5.0/nas")
    GMD = ("gmd", "http://www.isotc211.org/2005/gmd")
    GCO = ("gco", "http://www.isotc211.org/2005/gco")
    ISM = ("ism", "urn:us:gov:ic:ism")
    NTK = ("ntk", "urn:us:gov:ic:ntk")


class Tags(object):
    """
    Tags for NMIS elements in xml
    """

    class Extent(object):
        """
        The Extent tags for NMIS in xml
        """
        LON = "BoundLongitude"
        LAT = "BoundLatitude"
        W_BOUND_LON = "west" + LON
        E_BOUND_LON = "east" + LON
        N_BOUND_LAT = "north" + LAT
        S_BOUND_LAT = "south" + LAT

        DECIMAL = "Decimal"

    DATE_STAMP = "dateStamp"
    DATETIME = "DateTime"
    CHAR_STRING = "CharacterString"


class BoundingBox(object):
    """
    Bounding Box information, where it identifies the bounds of the data
    """

    def __init__(self,
                 min_x,
                 min_y,
                 max_x,
                 max_y):
        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_y


# TODO the overall design of the generator should be re-done.  I think that it should take a GeoPackage Path and simply
# construct the metadata by reading directly from the GeoPackage (finding all the tiles tables) instead of the user
# having to add the layer identity each time.

class Generator:
    """
    NSG Metadata generator:

    make as many calls to add_layer_identity which creates the metadata for that
    tiles layer that is stored in the GeoPackage.  When finished adding tiles layers,
    call write_metadata() so the metadata is written to the GeoPackage.
    """

    def __init__(self, geopackage_path, log=None):
        """
        :param geopackage_path: the file path for the geopackaging we are working on
        :param srs_name: The code value for the SRS (CODE: 4326 in EPSG:4326)
        :param srs_org: The organization specifying the SRS (ORG: EPSG in EPSG:4326)
        :param log: an optional log file passed through from an outer context
        """
        self.geopackage_path = geopackage_path
        self.log = log

        # TODO: Check that the existing Metadata has appropriate Namespaces and is NSG compliant
        # currently always gets the first item in the metadata list
        existing_metadata = next(iter(self.__load_metadata()), None)

        # register the namespaces we will be using as we manipulate the data
        [register_namespace(namespace.value[0], namespace.value[1]) for namespace in NameSpaces]
        # check to see if there is existing data or not
        if existing_metadata:
            self.tree = DET.fromstring(existing_metadata.metadata.encode('ascii', 'ignore'))
        else:
            self.tree = DET.parse(source=MD_TREE).getroot()  # Load base MD XML
            # set the creation date
            self.tree.set(QName(NameSpaces.ISM.value[1], "createDate"),
                          datetime.date.today().isoformat())

            # Fill out our DateStamp elem
            DATE_STAMP = self.__build_tag(namespace=NameSpaces.GMD.value[1],
                                          tag=Tags.DATE_STAMP,
                                          parent=self.tree)
            self.__build_tag(namespace=NameSpaces.GCO.value[1],
                             tag="Date",
                             parent=DATE_STAMP,
                             text=str(datetime.date.today().isoformat()))

    def __load_metadata(self):
        """
        Finds any existing metadata and returns it, otherwise returns an empty string.

        This will grab all the entries in the gpkg_metadata Table
        :return: a list of Metadata in the GeoPackage
        :rtype: list of Metadata
        """
        with get_database_connection(self.geopackage_path) as db:
            cursor = db.cursor()
            return GeoPackageMetadata.get_all_metadata(cursor=cursor)

    def write_metadata(self):
        """
        Generates the metadata tables and adds the NSG metadata to the extensions table.
        Also for any calls to add_layer_identity it adds that data as well. Be sure to
        add layer identity information before calling this method, since this writes to the
        GeoPackage
        """
        with get_database_connection(self.geopackage_path) as db:
            # Add entry to specify that this GeoPackage supports the Metadata extension
            try:
                cursor = db.cursor()

                GeoPackageMetadata.create_metadata_table(cursor=cursor)
                GeoPackageMetadataReference.create_metadata_reference_table(cursor=cursor)

                db.commit()
            except sqlite3.OperationalError:
                if self.log:
                    self.log.info("Failed to add the metadata entry to the extension table")
                    raise
            except sqlite3.IntegrityError:
                if self.log:
                    self.log.info("Failed to add the metadata entry to the extension table")

            # Add metadata entries
            try:
                root = self.tree
                xml_tostring = tostring(root, encoding='utf8', method='xml')
                GeoPackageMetadata.insert_or_update_metadata_row(cursor=cursor,
                                                                 metadata=NsgMetadata(metadata=xml_tostring))

                GeoPackageMetadataReference.insert_or_update_metadata_reference_row(cursor=cursor,
                                                                                    metadata_reference=NsgMetadataReference())

                db.commit()
            except sqlite3.IntegrityError:
                if self.log:
                    self.log.error("Failed to add NSG profile metadata to the metadata tables")

    def add_layer_identity(self,
                           layer_table_name,
                           abstract_msg,
                           BBOX,
                           srs_id,
                           srs_organization,
                           organization_name="UNDEFINED"):
        """
        Adds necessary XML on a per layer basis.

        :param organization_name: The name of the organization providing the data
        :type organization_name: str

        :param srs_organization: Case-insensitive name of the defining organization e.g. EPSG or epsg
        :type srs_organization: str

        :param srs_id: Unique identifier for each Spatial Reference System within a GeoPackage e.g. 4326
        :type srs_id: str

        :param layer_table_name: The table name where this layer's data is stored in the GPKG
        :type layer_table_name: str

        :param abstract_msg: string data added to give information about the layer
        :type abstract_msg: str

        :param BBOX: bbox representing the extent of the layer's data.
        :type BBOX: BoundingBox
        """
        self.__add_reference_system(srs_id=srs_id,
                                    srs_organization=srs_organization)

        self.__add_table_data(layer_table_name=layer_table_name, abstract_msg=abstract_msg, BBOX=BBOX,
                              organization_name=organization_name)

    def __add_reference_system(self, srs_id, srs_organization):
        """
        Adds the Spatial Reference information data to the XML.
        Will not add if the Spatial reference system is already in the XML (no duplicates)

        :param srs_id: Unique identifier for each Spatial Reference System within a GeoPackage e.g. 4326
        :type srs_id: str
        :param srs_organization: Case-insensitive name of the defining organization e.g. EPSG or epsg
        :type srs_organization: str
        """
        # attempt to find reference system specifications
        reference_sys = Generator.find_all_spatial_reference_system_ri_identifier_tags(root=self.tree)

        sys_present = False
        if reference_sys:  # if any reference systems are present, check to see if our added one is already listed
            for sys in reference_sys:
                org = Generator.find_code_space_from_ri_identifier_tag(ri_identifier_element=sys).text
                code = Generator.find_code_from_ri_identifer_tag(ri_identifier_element=sys).text
                if srs_id == code and srs_organization == org:
                    sys_present = True

        if sys_present:
            return
        # add the spatial reference system to the xml
        base = DET.parse(source=REFERENCE_SYS_TREE)
        self.tree.append(base.getroot())

        RS_IDENTIFIER = base.find("{gmd}:MD_ReferenceSystem/{gmd}:referenceSystemIdentifier/"
                                  "{gmd}:RS_Identifier".format(gmd=NameSpaces.GMD.value[0]),
                                  Generator.generate_namespace_map())
        self.__build_tag(namespace=NameSpaces.GCO.value[1],
                         tag=Tags.CHAR_STRING,
                         parent=RS_IDENTIFIER.find("{gmd}:code".format(gmd=NameSpaces.GMD.value[0]),
                                                   Generator.generate_namespace_map()),
                         text=srs_id)
        self.__build_tag(namespace=NameSpaces.GCO.value[1],
                         tag=Tags.CHAR_STRING,
                         parent=RS_IDENTIFIER.find("{gmd}:codeSpace".format(gmd=NameSpaces.GMD.value[0]),
                                                   Generator.generate_namespace_map()),
                         text=srs_organization)

    def __add_table_data(self,
                         layer_table_name,
                         abstract_msg,
                         BBOX,
                         organization_name):
        """
        Adds or updates the existing table data with the given information.

        :param organization_name: the name of the organization providing the data
        :type organization_name: str

        :param layer_table_name: the name of the raster tile layer which should match the table_name in the GeoPackage
        :type layer_table_name: str

        :param abstract_msg: string data added to give information about the layer
        :type abstract_msg: str

        :param BBOX: The bounds of the tile data
        :type BBOX: BoundingBox
        """
        # update existing table otherwise create a
        existing_table = self.find_table_identity(self.tree, layer_table_name)
        if existing_table:
            self.__update_table_data(table_identity=existing_table, layer_table_name=layer_table_name,
                                     abstract_msg=abstract_msg, BBOX=BBOX, organization_name=organization_name)
        else:
            self.__add_new_table_data(layer_table_name=layer_table_name, abstract_msg=abstract_msg, BBOX=BBOX,
                                      organization_name=organization_name)

    def __add_new_table_data(self,
                             layer_table_name,
                             abstract_msg,
                             BBOX,
                             organization_name):
        """
        Adds a new xml element about the table data to the metadata information

        :param organization_name:
        :param layer_table_name: the name of the raster tile layer which should match the table_name in the GeoPackage
        :type layer_table_name: str

        :param abstract_msg: string data added to give information about the layer
        :type abstract_msg: str

        :param BBOX: The bounds of the tile data
        :type BBOX: BoundingBox
        """
        # get the MD_DataIdentification element- where all the table information is stored
        # the table information needed are the following: CI_CITATION, ABSTRACT, ORG_NAME, and the BOUNDING BOX data
        base = DET.parse(source=LAYER_IDENTITY_TREE) \
            .find("{nas}:MD_DataIdentification".format(nas=NameSpaces.NAS.value[0]), Generator.generate_namespace_map())

        self.tree.append(base)

        namespace = NameSpaces.GCO.value[1]
        CI_CITATION = Generator.find_ci_citation(base)
        # add the title which should be the name of the table
        Generator.__build_tag(namespace=namespace,
                              tag=Tags.CHAR_STRING,
                              parent=CI_CITATION.find("{gmd}:title".format(gmd=NameSpaces.GMD.value[0]),
                                                      Generator.generate_namespace_map()),
                              text=layer_table_name)

        # add todays date of when the info was created/updated
        Generator.__build_tag(namespace=namespace,
                              tag=Tags.DATETIME,
                              parent=CI_CITATION.find(
                                  "{gmd}:date/{gmd}:CI_Date/gmd:date".format(gmd=NameSpaces.GMD.value[0]),
                                  Generator.generate_namespace_map()),
                              text=datetime.datetime.now().isoformat())

        # add the abstract information about the layer
        ABSTRACT = Generator.find_abstract_element(base)
        Generator.__build_tag(namespace=namespace,
                              tag=Tags.CHAR_STRING,
                              parent=ABSTRACT,
                              text=abstract_msg)

        # add the organization name
        ORG_NAME = Generator.find_organization_element(base)
        Generator.__build_tag(namespace=namespace,
                              tag=Tags.CHAR_STRING,
                              parent=ORG_NAME,
                              text=organization_name)

        # add the bounding box information
        Generator.__add_bounding_box_data(base=base, BBOX=BBOX)

    @staticmethod
    def __update_table_data(table_identity,
                            layer_table_name,
                            abstract_msg,
                            BBOX,
                            organization_name):
        """
        updates an existing table metadata information in the xml

        :param organization_name: the name of the organization providing the data
        :type organization_name: str

        :param table_identity: The existing MD_Identification element that is the parent of the table information
        element that needs to be updated.
        :type table_identity: Element

        :param layer_table_name: the name of the raster tile layer which should match the table_name in the GeoPackage
        :type layer_table_name: str

        :param abstract_msg: string data added to give information about the layer
        :type abstract_msg: str

        :param BBOX: The bounds of the tile data
        :type BBOX: BoundingBox
        """
        existing_ci_citation = Generator.find_ci_citation(table_identity)
        # update title
        title = existing_ci_citation.find(".//{gmd}:title/{gco}:{char_str}".format(gmd=NameSpaces.GMD.value[0],
                                                                                   gco=NameSpaces.GCO.value[0],
                                                                                   char_str=Tags.CHAR_STRING),
                                          Generator.generate_namespace_map())
        title.text = layer_table_name

        # update date
        date = existing_ci_citation.find(
            ".//{gmd}:date/{gmd}:CI_Date/{gmd}:date/{gco}:{date_time}".format(gmd=NameSpaces.GMD.value[0],
                                                                              gco=NameSpaces.GCO.value[0],
                                                                              date_time=Tags.DATETIME),
            Generator.generate_namespace_map())
        date.text = datetime.datetime.now().isoformat()

        existing_abstract_element = Generator.find_abstract_element(data_identification_element=table_identity)
        # update abstract message
        message = existing_abstract_element.find(".//{gco}:{char_string}".format(gco=NameSpaces.GCO.value[0],
                                                                                 char_string=Tags.CHAR_STRING),
                                                 Generator.generate_namespace_map())
        message.text = abstract_msg

        existing_organization_element = Generator.find_organization_element(data_identification_element=table_identity)
        # update organization name
        organization_name_element = existing_organization_element.find(".//{gco}:{char_string}"
                                                                       .format(gco=NameSpaces.GCO.value[0],
                                                                               char_string=Tags.CHAR_STRING),
                                                                       Generator.generate_namespace_map())
        organization_name_element.text = organization_name

        existing_bounding_box_element = Generator.find_bounding_box_tag(data_identification_element=table_identity)
        # update bounds

        # north
        north = existing_bounding_box_element.find(
            ".//{tag}:{name}/{tag2}:{decimal}".format(tag=NameSpaces.GMD.value[0],
                                                      name=Tags.Extent.N_BOUND_LAT,
                                                      tag2=NameSpaces.GCO.value[0],
                                                      decimal=Tags.Extent.DECIMAL),
            Generator.generate_namespace_map())
        north.text = str(BBOX.max_y)
        # south
        south = existing_bounding_box_element.find(
            ".//{tag}:{name}/{tag2}:{decimal}".format(tag=NameSpaces.GMD.value[0],
                                                      name=Tags.Extent.S_BOUND_LAT,
                                                      tag2=NameSpaces.GCO.value[0],
                                                      decimal=Tags.Extent.DECIMAL),
            Generator.generate_namespace_map())
        south.text = str(BBOX.min_y)
        # east
        east = existing_bounding_box_element.find(
            ".//{tag}:{name}/{tag2}:{decimal}".format(tag=NameSpaces.GMD.value[0],
                                                      name=Tags.Extent.E_BOUND_LON,
                                                      tag2=NameSpaces.GCO.value[0],
                                                      decimal=Tags.Extent.DECIMAL),
            Generator.generate_namespace_map())
        east.text = str(BBOX.max_x)
        # west
        west = existing_bounding_box_element.find(
            ".//{tag}:{name}/{tag2}:{decimal}".format(tag=NameSpaces.GMD.value[0],
                                                      name=Tags.Extent.W_BOUND_LON,
                                                      tag2=NameSpaces.GCO.value[0],
                                                      decimal=Tags.Extent.DECIMAL),
            Generator.generate_namespace_map())
        west.text = str(BBOX.min_x)

    @staticmethod
    def __add_bounding_box_data(base, BBOX):
        """
        Adds the extent information to a particular MD_DataIdentification element (which is information about a
        specific layer or raster tiles table)

        :param base: MD_DataIdentification Element that the Extent information needs to be appended to
        :type base: Element
        :param BBOX: The tile bounds
        :type BBOX: BoundingBox
        """
        namespace = NameSpaces.GMD.value[1]
        EX_GEO_BOUNDING_BOX = Generator.find_bounding_box_tag(data_identification_element=base)

        W_BOUND_LON = Generator.__build_tag(namespace=namespace, tag=Tags.Extent.W_BOUND_LON,
                                            parent=EX_GEO_BOUNDING_BOX)
        E_BOUND_LON = Generator.__build_tag(namespace=namespace, tag=Tags.Extent.E_BOUND_LON,
                                            parent=EX_GEO_BOUNDING_BOX)
        N_BOUND_LAT = Generator.__build_tag(namespace=namespace, tag=Tags.Extent.N_BOUND_LAT,
                                            parent=EX_GEO_BOUNDING_BOX)
        S_BOUND_LAT = Generator.__build_tag(namespace=namespace, tag=Tags.Extent.S_BOUND_LAT,
                                            parent=EX_GEO_BOUNDING_BOX)

        namespace = NameSpaces.GCO.value[1]
        Generator.__build_tag(namespace=namespace, tag=Tags.Extent.DECIMAL, parent=W_BOUND_LON, text=str(BBOX.min_x))
        Generator.__build_tag(namespace=namespace, tag=Tags.Extent.DECIMAL, parent=E_BOUND_LON, text=str(BBOX.max_x))
        Generator.__build_tag(namespace=namespace, tag=Tags.Extent.DECIMAL, parent=N_BOUND_LAT, text=str(BBOX.max_y))
        Generator.__build_tag(namespace=namespace, tag=Tags.Extent.DECIMAL, parent=S_BOUND_LAT, text=str(BBOX.min_y))

    @staticmethod
    def find_all_spatial_reference_system_ri_identifier_tags(root):
        """
        returns a list of Elements with the tag RS_Identifier
        :param root: root xml element of the tree
        :type root: Element
        :return: a list of Elements with the tag RS_Identifier
        :rtype: list of Element
        """
        return root.findall(".//{gmd}:referenceSystemInfo"
                            "/{gmd}:MD_ReferenceSystem"
                            "/{gmd}:referenceSystemIdentifier"
                            "/{gmd}:RS_Identifier".format(gmd=NameSpaces.GMD.value[0]),
                            Generator.generate_namespace_map())

    @staticmethod
    def find_code_from_ri_identifer_tag(ri_identifier_element):
        """
        in
        <gmd:code>
            <gco:characterString>text</gco:characterString>
        </gmd:code>
        returns the characterString Element
         :param ri_identifier_element: the RI_Identifier element containing the code subElement
        :type ri_identifier_element: Element
        :return:
        in
        <gmd:code>
            <gco:characterString>text</gco:characterString>
        </gmd:code>
        returns the characterString Element
        :rtype: Element, None
        """
        return ri_identifier_element.find("{gmd}:code/{gco}:{char_string}".format(gmd=NameSpaces.GMD.value[0],
                                                                                  gco=NameSpaces.GCO.value[0],
                                                                                  char_string=Tags.CHAR_STRING),
                                          Generator.generate_namespace_map())

    @staticmethod
    def find_code_space_from_ri_identifier_tag(ri_identifier_element):
        """
        in
        <gmd:codeSpace>
            <gco:characterString>text</gco:characterString>
        </gmd:codeSpace>

        this returns the characterString Element
        :param ri_identifier_element: the RI_Identifier element containing the codeSpace subElement
        :type ri_identifier_element: Element
        :return: in
        <gmd:codeSpace>
            <gco:characterString>text</gco:characterString>
        </gmd:codeSpace>

        this returns the characterString Element
        :rtype: Element, None
        """
        return ri_identifier_element.find("{gmd}:codeSpace/{gco}:{char_string}".format(gmd=NameSpaces.GMD.value[0],
                                                                                       gco=NameSpaces.GCO.value[0],
                                                                                       char_string=Tags.CHAR_STRING),
                                          Generator.generate_namespace_map())

    @staticmethod
    def find_bounding_box_tag(data_identification_element):
        """
        Returns the Geographic Bounding Box element or None if it was not found in the base
        :param data_identification_element:  MD_DataIdentification Element that the EX_GeographBoundingBox will be part of
        (or a sub element of)
        :type data_identification_element: Element
        :return: Returns the Geographic Bounding Box element or None if it was not found in the base
        :rtype: Element, None
        """
        return data_identification_element.find("{gmd}:extent/"
                                                "{gmd}:EX_Extent/"
                                                "{gmd}:geographicElement/"
                                                "{gmd}:EX_GeographicBoundingBox".format(gmd=NameSpaces.GMD.value[0]),
                                                Generator.generate_namespace_map())

    @staticmethod
    def find_table_identity(base, table_name):
        """
        Returns the MD_DataIdentification Element that matches the table_name given.  Returns None if a match
        was not found
        :param base: The root of the xml
        :type base: Element
        :param table_name:
        :type table_name: str
        :return: MD_DataIdentification Element that the matches the table_name given, or None if nothing is found
        :rtype: Element, None
        """
        table_identities = base.findall(".//{nas}:MD_DataIdentification".format(nas=NameSpaces.NAS.value[0]),
                                        Generator.generate_namespace_map())
        for table_identity in table_identities:
            ci_citations = table_identity.findall(
                ".//{gmd}:citation/{gmd}:CI_Citation".format(gmd=NameSpaces.GMD.value[0]),
                Generator.generate_namespace_map())
            for ci_citation in ci_citations:
                existing_table_name = ci_citation.find(
                    "{gmd}:title/{gco}:{char_str}".format(gmd=NameSpaces.GMD.value[0],
                                                          gco=NameSpaces.GCO.value[0],
                                                          char_str=Tags.CHAR_STRING),
                    Generator.generate_namespace_map()) \
                    .text
                if table_name == existing_table_name:
                    return table_identity

        return None

    @staticmethod
    def find_ci_citation(data_identification_element):
        """
        Gets the Ci_Citation sub element given the MD_DataIdentification Element
        :param data_identification_element: MD_DataIdentification Element
        :type data_identification_element: Element
        :return:  Gets the Ci_Citation sub element given the MD_DataIdentification Element
        :rtype: Element, None
        """
        return data_identification_element.find("{gmd}:citation/{gmd}:CI_Citation".format(gmd=NameSpaces.GMD.value[0]),
                                                Generator.generate_namespace_map())

    @staticmethod
    def find_abstract_element(data_identification_element):
        """
        Gets the abstract sub element given the MD_DataIdentification Element
        :param data_identification_element: MD_DataIdentification Element
        :type data_identification_element: Element
        :return:   Gets the abstract sub element given the MD_DataIdentification Element
        :rtype: Element, None
        """
        return data_identification_element.find("{gmd}:abstract".format(gmd=NameSpaces.GMD.value[0]),
                                                Generator.generate_namespace_map())

    @staticmethod
    def find_organization_element(data_identification_element):
        """
        Gets the organizationName sub element given the MD_DataIdentification Element
        :param data_identification_element: MD_DataIdentification Element
        :type data_identification_element: Element
        :return:  Gets the organizationName sub element given the MD_DataIdentification Element
        :rtype: Element, None
        """
        return data_identification_element.find("{gmd}:pointOfContact/{gmd}:CI_ResponsibleParty/{gmd}:organisationName"
                                                .format(gmd=NameSpaces.GMD.value[0]),
                                                Generator.generate_namespace_map())

    @staticmethod
    def __build_tag(namespace,
                    tag,
                    parent=None,
                    text=None):
        """
        Returns the Element that was created with the properties given appended to the parent element given (or just
        the new element if no parent element was given)

        :param namespace: the namespace the new tag belongs to i.e. gmd, nas
        :type namespace: str

        :param tag: the name of the tag  i.e. abstract, CI_Citation
        :type tag: str

        :param parent: the parent Element that this new tag should be appended to
        :type parent: Element

        :param text: the text that should be in the new tag i.e. <namespace:tag>my cool text</namespace:tag>
        :type text: str

        :return: the Element that was created with the properties given appended to the parent element given (or just
        the new element if no parent element was given)
        :rtype: Element
        """
        q_name = QName(namespace, tag)
        if parent is None:
            e = Element(tag=q_name)
            if text:
                e.text = text
            return e
        else:
            e = SubElement(parent,
                           q_name,
                           {})
            if text:
                e.text = text
            return e

    @staticmethod
    def generate_namespace_map():
        return dict((namespace.value[0], namespace.value[1]) for namespace in NameSpaces)


dir_name = os.path.dirname(__file__)
REFERENCE_SYS_TREE = join(dir_name, 'resources', 'spatial_reference_system_tree.xml')
LAYER_IDENTITY_TREE = join(dir_name, 'resources', 'layer_identity_tree.xml')
MD_TREE = join(dir_name, 'resources', 'base_nsg_metadata.xml')
