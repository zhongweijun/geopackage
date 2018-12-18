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
    Steven D. Lander
    Jason Hall
    Jenifer Cochran
Date: 2014-08
Requires: Python Imaging Library (PIL or Pillow), Sqlite3
Description: Test cases for tiles2gpkg_parallel.py

Version:
"""
import argparse
import os
import shutil
from math import pi
from os import getcwd
from os import listdir
from os import mkdir
from os import remove
from os import walk
from os.path import abspath, dirname
from os.path import join
from random import randint
from sqlite3 import Binary
from sys import path
from sys import version_info

import pytest
from pytest import raises

from Testing.rgb_tiles import geodetic, mercator
from scripts.common.zoom_metadata import ZoomMetadata
from scripts.geopackage.geopackage import Geopackage
from scripts.geopackage.nsg_geopackage import NsgGeopackage
from scripts.geopackage.srs.ellipsoidal_mercator import EllipsoidalMercator
from scripts.geopackage.srs.geodetic import Geodetic
from scripts.geopackage.srs.mercator import Mercator
from scripts.geopackage.srs.scaled_world_mercator import ScaledWorldMercator
from scripts.geopackage.utility.sql_utility import get_database_connection, table_exists
from scripts.packaging.temp_db import TempDB
from scripts.packaging.tiles2gpkg_parallel import img_to_buf, img_has_transparency, file_count, split_all, worker_map, \
    build_lut, sqlite_worker, allocate, build_lut_nsg, combine_worker_dbs, main

if version_info[0] == 3:
    xrange = range
from tempfile import gettempdir
from uuid import uuid4

from PIL import ImageDraw
from PIL.Image import new
from PIL.Image import open as iopen

path.append(abspath("Packaging"))

GEODETIC_FILE_PATH = dirname(geodetic.__file__)
MERCATOR_FILE_PATH = dirname(mercator.__file__)
DEFAULT_TILES_TABLE_NAME = "tiles table"

# testing commands:
# py.test --cov-report term-missing \
#         --cov tiles2gpkg_parallel test_tiles2gpkg.py


class TestMercator:
    """Test the Mercator object."""

    def test_tile_size(self):
        """Test tile size default."""
        merc = Mercator()
        assert merc.tile_size == 256

    def test_radius(self):
        """Test radius for mercator."""
        merc = Mercator()
        assert merc.radius == 6378137

    def test_origin_shift(self):
        """Test origin shift calculation."""
        merc = Mercator()
        assert merc.origin_shift == pi * merc.radius

    def test_init_res(self):
        """Test initial resolution calculation."""
        merc = Mercator()
        assert merc.initial_resolution == 2 * \
               merc.origin_shift / merc.tile_size

    def test_invert_y_one(self):
        """Test inverted Y axis calculation."""
        z = 1
        y = 0
        assert Mercator.invert_y(z, y) == 1

    def test_invert_y_two(self):
        """Test a more complicated Y axis inversion."""
        z = 13
        y = 31
        assert Mercator.invert_y(z, y) == 8160

    def test_pixel_size(self):
        """Test pixel size calculation."""
        z = randint(0, 21)
        result = Mercator.pixel_size(z)
        assert result * 2 ** z == 156543.033928041

    def test_tile_to_lat_lon_one(self):
        """Test conversion from tile coordinate to lat/lon."""
        z = x = y = 0
        lat, lon = Mercator.tile_to_lat_lon(z, x, y)
        assert lon == -180.0 and lat == -85.0511287798066

    def test_tile_to_lat_lon_two(self):
        """Test the top right corner of zoom 0."""
        z = 0
        x = y = 1
        lat, lon = Mercator.tile_to_lat_lon(z, x, y)
        assert lon == 180.0 and lat == 85.0511287798066
        z = 14
        x = 11332
        y = 9870
        lat, lon = Mercator.tile_to_lat_lon(z, x, y)
        assert lon == 68.994140625 and \
               lat == 34.56085936708385

    def test_tile_to_lat_lon_four(self):
        """Test a random tile to lat/lon."""
        z = 14
        x = 11333
        y = 9871
        lat, lon = Mercator.tile_to_lat_lon(z, x, y)
        assert lon == 69.01611328125 and \
               lat == 34.57895241036947

    def test_tile_to_meters_one(self):
        """Test conversion from tile coordinate to meters."""
        merc = Mercator()
        z = x = y = 0
        mx, my = merc.tile_to_meters(z, x, y)
        mx = merc.truncate(mx)
        my = merc.truncate(my)
        assert float(mx) == -20037508.34 and \
               float(my) == -20037508.34

    def test_tile_to_meters_two(self):
        """Test conversion with a different tile coord to meters."""
        merc = Mercator()
        z = 0
        x = y = 1
        mx, my = merc.tile_to_meters(z, x, y)
        mx = merc.truncate(mx)
        my = merc.truncate(my)
        assert float(mx) == 20037508.34 and \
               float(my) == 20037508.34

    def test_tile_to_meters_three(self):
        """Test a random tile to meters."""
        merc = Mercator()
        z = 14
        x = 11332
        y = 9870
        mx, my = merc.tile_to_meters(z, x, y)
        mx = merc.truncate(mx)
        my = merc.truncate(my)
        assert float(mx) == 7680392.60 and \
               float(my) == 4104362.67

    def test_tile_to_meters_four(self):
        """Test another corner of a random tile to meters."""
        merc = Mercator()
        z = 14
        x = 11333
        y = 9871
        mx, my = merc.tile_to_meters(z, x, y)
        mx = merc.truncate(mx)
        my = merc.truncate(my)
        assert float(mx) == 7682838.58 and \
               float(my) == 4106808.65

    def test_truncate(self):
        """Test mercator accuracy truncation."""
        merc = Mercator()
        f = 1234.567890123
        result = merc.truncate(f)
        assert float(result) == 1234.56

    def test_get_coord_one(self):
        """Test get coordinate from tile method."""
        merc = Mercator()
        z = x = y = 0
        mx, my = merc.get_coord(z, x, y)
        mx = merc.truncate(mx)
        my = merc.truncate(my)
        assert float(mx) == -20037508.34 and \
               float(my) == -20037508.34

    def test_get_coord_two(self):
        """Test get coord with a random tile."""
        merc = Mercator()
        z = 14
        x = 11332
        y = 9870
        mx, my = merc.get_coord(z, x, y)
        mx = merc.truncate(mx)
        my = merc.truncate(my)
        assert float(mx) == 7680392.60 and \
               float(my) == 4104362.67


class TestGeodetic:
    """Test the Geodetic object."""

    def test_tile_size(self):
        geod = Geodetic()
        assert geod.tile_size == 256

    def test_res_fact(self):
        geod = Geodetic()
        assert geod.resolution_factor == 360.0 / (geod.tile_size)

    def test_pixel_size(self):
        geod = Geodetic()
        z = randint(0, 21)
        result = geod.pixel_size(z)
        assert 2 ** z * result == geod.resolution_factor

    def test_get_coord_one(self):
        geod = Geodetic()
        z = 1
        x = y = 0
        lon, lat = geod.get_coord(z, x, y)
        assert lon == -180.0 and lat == -90.0

    def test_get_coord_two(self):
        geod = Geodetic()
        z = x = y = 1
        lon, lat = geod.get_coord(z, x, y)
        assert lon == 0 and lat == 90

    def test_get_coord_three(self):
        geod = Geodetic()
        z = 21
        x = 599187
        y = 749974
        lon, lat = geod.get_coord(z, x, y)
        lon = geod.truncate(lon)
        lat = geod.truncate(lat)
        assert float(lon) == -77.1427345 and \
               float(lat) == 38.7415695

    def test_get_coord_four(self):
        geod = Geodetic()
        z = 21
        x = 599188
        y = 749975
        lon, lat = geod.get_coord(z, x, y)
        lon = geod.truncate(lon)
        lat = geod.truncate(lat)
        assert float(lon) == -77.1425628 and \
               float(lat) == 38.7417411

    def test_invert_y_one(self):
        z = 2
        y = 0
        assert Geodetic.invert_y(z, y) == 1

    def test_invert_y_two(self):
        z = y = 0
        assert Geodetic.invert_y(z, y) == 0

    def test_truncate(self):
        x = 12.34567890
        result = Geodetic.truncate(x)
        assert float(result) == 12.3456789


class TestEllipsoidalMercator:
    """Test the Ellipsoidal Mercator object."""

    def test_lat_to_northing(self):
        # TODO: need input from Micah
        return True

    def test_tile_to_meters_one(self):
        ellip = EllipsoidalMercator()
        z = x = y = 0
        mx, my = ellip.tile_to_meters(z, x, y)
        mx = ellip.truncate(mx)
        my = ellip.truncate(my)
        assert float(mx) == -20037508.34 and \
               float(my) == -20037508.34

    def test_tile_to_meters_two(self):
        ellip = EllipsoidalMercator()
        z = 0
        x = y = 1
        mx, my = ellip.tile_to_meters(z, x, y)
        mx = ellip.truncate(mx)
        my = ellip.truncate(my)
        assert float(mx) == 20037508.34 and \
               float(my) == 20037508.34

    def test_tile_to_lat_lon_one(self):
        z = x = y = 0
        lat, lon = EllipsoidalMercator.tile_to_lat_lon(z, x, y)
        assert lon == -180.0 and \
               lat == -85.08405904978349

    def test_tile_to_lat_lon_two(self):
        z = 0
        x = y = 1
        lat, lon = EllipsoidalMercator.tile_to_lat_lon(z, x, y)
        assert lon == 180.0 and \
               lat == 85.08405904978349

    def test_tile_to_lat_lon_three(self):
        # Visually verified that this tile
        # should be near Galva, Illinois
        z = 3
        x = 2
        y = 5
        lat, lon = EllipsoidalMercator.tile_to_lat_lon(z, x, y)
        assert lat == 41.170427276143315 and \
               lon == -90.0

    def test_tile_to_lat_lon_four(self):
        # Visually verified to show an
        # Antarctic tile
        z = 7
        x = 114
        y = 31
        lat, lon = EllipsoidalMercator.tile_to_lat_lon(z, x, y)
        assert lat == -67.7443134783405 and \
               lon == 140.625

    def test_tile_to_lat_lon_five(self):
        # AGC
        z = 17
        x = 37448
        y = 80770
        lat, lon = EllipsoidalMercator.tile_to_lat_lon(z, x, y)
        assert lat == 38.74009055509699 and \
               lon == -77.14599609375


class TestScaledWorldMercator:
    """Test the Scaled World Mercator object."""

    def test_lat_to_northing(self):
        # TODO: Input needed from Micah
        return True

    def test_pixel_size(self):
        z = randint(0, 21)
        assert 2 ** z * ScaledWorldMercator.pixel_size(z) == 125829.12

    def test_tile_to_lat_lon_one(self):
        z = x = y = 0
        lat, lon = ScaledWorldMercator.tile_to_lat_lon(z, x, y)
        lat_result = Geodetic.truncate(lat)
        assert float(lat_result) == -85.0840590 and \
               lon == -180.0

    def test_tile_to_lat_lon_two(self):
        z = 0
        x = y = 1
        lat, lon = ScaledWorldMercator.tile_to_lat_lon(z, x, y)
        lat_result = Geodetic.truncate(lat)
        assert float(lat_result) == 85.0840590 and \
               lon == 180.0

    def test_tile_to_meters_one(self):
        # TODO: this should return -16106127.36
        scal = ScaledWorldMercator()
        z = x = y = 0
        expected = -17179869.18
        mx, my = scal.tile_to_meters(z, x, y)
        mx = ScaledWorldMercator.truncate(mx)
        my = round(my, 2)
        assert float(mx) == expected and float(my) == expected


class TestZoomMetadata:
    """Test the ZoomMetadata object."""

    def test_zoom_meta_data_zoom(self):
        zmd = make_zmd()
        assert zmd.zoom is 1

    def test_zoom_meta_data_min_tile_col(self):
        zmd = make_zmd()
        assert zmd.min_tile_col is 1

    def test_zoom_meta_data_min_tile_row(self):
        zmd = make_zmd()
        assert zmd.min_tile_row is 1

    def test_zoom_meta_data_min_x(self):
        zmd = make_zmd()
        assert zmd.min_x is 1

    def test_zoom_meta_data_min_y(self):
        zmd = make_zmd()
        assert zmd.min_y is 1

    def test_zoom_meta_data_max_tile_col(self):
        zmd = make_zmd()
        assert zmd.max_tile_col is 2

    def test_zoom_meta_data_max_tile_row(self):
        zmd = make_zmd()
        assert zmd.max_tile_row is 2

    def test_zoom_meta_data_max_x(self):
        zmd = make_zmd()
        assert zmd.max_x is 2

    def test_zoom_meta_data_max_y(self):
        zmd = make_zmd()
        assert zmd.max_y is 2


class Testgeopackage:
    """Test the Geopackage object."""

    def test_file_path(self):
        filename = uuid4().hex + '.gpkg'
        tmp_dir = gettempdir()
        tmp_file = join(tmp_dir, filename)
        gpkg = Geopackage(tmp_file, 3857, DEFAULT_TILES_TABLE_NAME)
        assert gpkg.file_path == tmp_file
        os.remove(tmp_file)

    def test_assimilate_error(self, make_session_folder):
        session_folder = join(gettempdir(), make_session_folder, "test.gpkg")
        with Geopackage(session_folder, 3395, DEFAULT_TILES_TABLE_NAME) as gpkg:
            with raises(IOError):
                gpkg.assimilate("None")

    def test_execute_return(self, make_session_folder):
        session_folder = join(gettempdir(), make_session_folder, "test.gpkg")
        gpkg = Geopackage(session_folder, 9804, DEFAULT_TILES_TABLE_NAME)
        gpkg.initialize()
        result = gpkg.execute("select count(*) from '{table}';".format(table=DEFAULT_TILES_TABLE_NAME))
        assert (result.fetchone())[0] == 0

    def test_execute_with_inputs(self, make_gpkg):
        gpkg = make_gpkg
        gpkg.initialize()
        test_statement = """
            UPDATE gpkg_contents SET
                min_x = ?,
                min_y = ?,
                max_x = ?,
                max_y = ?
            WHERE table_name = '{table_name}';
        """.format(table_name=DEFAULT_TILES_TABLE_NAME)
        result = gpkg.execute(test_statement, (1, 1, 2, 2))
        assert result.fetchone() is None

    def test_update_metadata(self, make_gpkg):
        zmd_list = []
        for _ in xrange(5):
            zmd_list.append(make_zmd())
        gpkg = make_gpkg
        gpkg.initialize()
        gpkg.update_metadata(zmd_list)
        cursor = gpkg.execute("select min_x from gpkg_contents")
        assert cursor.fetchone()[0] == 1.0

    def test_matrix_width(self, make_gpkg):
        test_width_stmt = """
            SELECT matrix_width
            FROM gpkg_tile_matrix
            WHERE zoom_level is ?;
        """
        gpkg = make_gpkg
        gpkg.initialize()
        gpkg.update_metadata(make_zmd_list_geodetic())
        for zoom in xrange(2, 6):
            (result,) = gpkg.execute(test_width_stmt, (zoom,))
            width = (2 ** zoom)
            if result[0] != width:
                print(zoom, result[0], width)
                assert False
        assert True

    def test_matrix_height(self, make_gpkg):
        test_height_stmt = """
            SELECT matrix_height
            FROM gpkg_tile_matrix
            WHERE zoom_level is ?;
        """
        gpkg = make_gpkg
        gpkg.initialize()
        gpkg.update_metadata(make_zmd_list_geodetic())
        for zoom in xrange(2, 6):
            (result,) = gpkg.execute(test_height_stmt, (zoom,))
            height = (2 ** (zoom - 1))
            if result[0] != height:
                print(zoom, result[0], height)
                assert False
            assert True

    class TestNSGGeopackage:
        """Test the Geopackage object. (NSG version)"""

        def test_gpkg_contents(self, make_gpkg_nsg):
            test_gpkg_contents_stmt = """
                SELECT min_x, min_y, max_x, max_y
                FROM gpkg_contents
            """
            gpkg = make_gpkg_nsg
            gpkg.initialize()
            gpkg.update_metadata(make_zmd_list_geodetic())
            (result,) = gpkg.execute(test_gpkg_contents_stmt)
            assert result[0] == 0
            assert result[1] == 0
            assert result[2] == 15
            assert result[3] == 31

        def test_gpkg_metadata(self, make_gpkg_nsg):
            test_gpkg_metadata_stmt = """
                SELECT md_scope, md_standard_uri, mime_type
                FROM gpkg_metadata
            """
            gpkg = make_gpkg_nsg
            gpkg.initialize()
            gpkg.update_metadata(make_zmd_list_geodetic())
            (result,) = gpkg.execute(test_gpkg_metadata_stmt)
            assert result[0] == 'series'
            assert result[1] == 'http://metadata.ces.mil/dse/ns/GSIP/nmis/2.2.0/doc'
            assert result[2] == 'text/xml'

        def test_gpkg_tilematrixset(self, make_gpkg_nsg):
            test_gpkg_metadata_stmt = """
                SELECT *
                FROM gpkg_tile_matrix_set
            """
            gpkg = make_gpkg_nsg
            gpkg.initialize()
            gpkg.update_metadata(make_zmd_list_geodetic())
            (result,) = gpkg.execute(test_gpkg_metadata_stmt)
            assert result[0] == DEFAULT_TILES_TABLE_NAME
            assert result[1] == 4326
            assert result[2] == -180
            assert result[3] == -90
            assert result[4] == 180
            assert result[5] == 90

        def test_gpkg_extensions(self, make_gpkg_nsg):
            test_gpkg_metadata_stmt = """
                SELECT extension_name, definition, scope, table_name
                FROM gpkg_extensions
            """
            gpkg = make_gpkg_nsg
            gpkg.initialize()
            gpkg.update_metadata(make_zmd_list_geodetic())
            (result, result2) = gpkg.execute(test_gpkg_metadata_stmt)
            assert result[0] == 'gpkg_metadata'
            assert result[1] == 'http://www.geopackage.org/spec121/#extension_metadata'
            assert result[2] == 'read-write'
            assert result[3] == 'gpkg_metadata'
            assert result2[0] == 'gpkg_metadata'
            assert result2[1] == 'http://www.geopackage.org/spec121/#extension_metadata'
            assert result2[2] == 'read-write'
            assert result2[3] == 'gpkg_metadata_reference'


class TestTempDB:
    """Test the TempDB object."""

    def __make_tempDB(self):
        temp_folder = uuid4().hex
        temp_db_folder = join(gettempdir(), temp_folder)
        mkdir(temp_db_folder)
        return temp_db_folder, TempDB(temp_db_folder, DEFAULT_TILES_TABLE_NAME)

    def test_insert_image_blob(self):
        img = new("RGB", (256, 256), "red")
        data = img_to_buf(img, 'jpeg').read()
        temp_db_folder, tempDB = self.__make_tempDB()
        tempDB.insert_image_blob(0, 0, 0, Binary(data))
        result = tempDB.execute("select count(*) from '{table}';".format(table=DEFAULT_TILES_TABLE_NAME))
        assert result.fetchone()[0] == 1
        shutil.rmtree(temp_db_folder)



class TestImgToBuf:
    """Test the img_to_buf method."""

    def test_img_to_buf_jpg(self):
        img = new("RGB", (256, 256), "red")
        data = img_to_buf(img, 'jpeg').read()
        # a 'JFIF' chunk in the bitstream indicates a .jpg image
        assert b'JFIF' in data

    def test_img_to_buf_png(self):
        img = new("RGB", (256, 256), "red")
        img.save("test1.png", 'PNG')
        data = img_to_buf(img, 'png').read()
        # ImageHeaDeR, ImageDATa, and ImageEND are
        # all necessary chunks in a .PNG bitstream
        assert b'IHDR' in data and b'IDAT' in data and b'IEND' in data
        remove("test1.png")

    def test_img_to_buf_source(self):
        img = new("RGB", (256, 256), "red")
        img.save("test2.jpg")
        img.format = "JPEG"
        data = img_to_buf(img, 'source').read()
        # a 'JFIF' chunk in the bitstream indicates a .jpg image
        assert b'JFIF' in data
        remove("test2.jpg")


class TestImgHasTransparency:
    """Test the img_has_transparency method."""

    def test_not_transparent(self):
        img = new("RGB", (256, 256), "red")
        assert img_has_transparency(img) == 0

    def test_partially_transparent(self):
        img = new("RGBA", (256, 256))
        draw = ImageDraw.Draw(img)
        draw.ellipse((96, 96, 160, 160), fill=(255, 0, 0))
        assert img_has_transparency(img) > 0

    def test_fully_transparent(self):
        img = new('RGBA', (256, 256))
        assert img_has_transparency(img) == -1

    def test_paletted_image_transparent(self):
        img = new("P", (256, 256), 0)
        img.save("test1.png", "PNG", transparency=b'\x00')
        img = iopen("test1.png", "r")
        assert img_has_transparency(img)
        remove("test1.png")

    def test_paletted_image_not_transparent(self):
        img = new('P', (256, 256))
        assert img_has_transparency(img) == 0


def test_file_count():
    assert len(file_count(MERCATOR_FILE_PATH)) == 4


def test_split_all():
    coords = ["1", "2", "3.png"]
    file_path = join(getcwd(), "data", coords[0], coords[1], coords[2])
    result = split_all(file_path)
    assert result['z'] == int(coords[0]) and \
           result['x'] == int(coords[1]) and \
           result['y'] == int(coords[2].split(".")[0]) and \
           result['path'] == file_path


def test_worker_map(make_session_folder):
    session_folder = join(gettempdir(), make_session_folder)
    tempdb = TempDB(session_folder, DEFAULT_TILES_TABLE_NAME)
    tile_dict = make_mercator_filelist()[0]
    tile_info = [make_zmd(), make_zmd()]
    imagery = 'mixed'
    invert_y = None
    extra_args = dict(tile_info=tile_info, imagery=imagery, jpeg_quality=75, nsg_profile=False, renumber=False)
    worker_map(tempdb, tile_dict, extra_args, invert_y)
    files = listdir(session_folder)
    # assert the worker_map function put the .gpkg.part file into the db
    assert len(files) == 1 and '.gpkg.part' in files[0]


class Testsqliteworker:
    """Test the sqlite_worker function."""

    def test_sqlite_worker_4326(self, make_session_folder):
        session_folder = join(gettempdir(), make_session_folder)
        file_list = make_geodetic_filelist()
        metadata = build_lut(file_list, True, 4326)
        extra_args = dict(root_dir=session_folder, tile_info=metadata,
                          lower_left=True, srs=4326, imagery='mixed',
                          jpeg_quality=75, nsg_profile=False, renumber=False, table_name='diff_table_name')
        sqlite_worker(file_list, extra_args)
        # assert that worker put the .gpkg.part file into base_dir
        files = listdir(session_folder)
        assert len(files) == 2 and '.gpkg.part' in files[0]

    def test_sqlite_worker_3857(self, make_session_folder):
        session_folder = join(gettempdir(), make_session_folder)
        file_list = make_geodetic_filelist()
        metadata = build_lut(file_list, True, 3857)
        extra_args = dict(root_dir=session_folder, tile_info=metadata,
                          lower_left=True, srs=3857, imagery='mixed',
                          jpeg_quality=75, nsg_profile=False, renumber=False, table_name='t a b l e')
        sqlite_worker(file_list, extra_args)
        files = listdir(session_folder)
        assert len(files) == 2 and '.gpkg.part' in files[0]

    def test_sqlite_worker_3395(self, make_session_folder):
        session_folder = join(gettempdir(), make_session_folder)
        file_list = make_geodetic_filelist()
        metadata = build_lut(file_list, True, 3395)
        extra_args = dict(root_dir=session_folder, tile_info=metadata,
                          lower_left=True, srs=3395, imagery='mixed',
                          jpeg_quality=75, nsg_profile=False, renumber=False, table_name='n am e')
        sqlite_worker(file_list, extra_args)
        files = listdir(session_folder)
        assert len(files) == 2 and '.gpkg.part' in files[0]

    def test_sqlite_worker_9804(self, make_session_folder):
        session_folder = join(gettempdir(), make_session_folder)
        file_list = make_geodetic_filelist()
        metadata = build_lut(file_list, True, 9804)
        extra_args = dict(root_dir=session_folder, tile_info=metadata,
                          lower_left=True, srs=9804, imagery='mixed',
                          jpeg_quality=75, nsg_profile=False, renumber=False, table_name='table-name')
        sqlite_worker(file_list, extra_args)
        files = listdir(session_folder)
        assert len(files) == 2 and '.gpkg.part' in files[0]


class TestAllocate:
    class MockPool:
        def __init__(self):
            self.works = True

        def apply_async(self, worker):
            raise TypeError("success")

    def test_allocate_one(self):
        cores = 4
        file_list = [1, 2]
        cpu_pool = self.MockPool()
        base_dir = gettempdir()
        extra_args = dict(root_dir=base_dir, tile_info=make_zmd(),
                          lower_left=True, srs=4326, imagery='mixed', table_name='table')
        e = None
        try:
            allocate(cores, cpu_pool, file_list, extra_args)
        except TypeError as e:
            print('success')
        else:
            assert e is not None and type(e) == TypeError


class TestBuildLut:
    """Test the build_lut function."""

    def test_build_lut_scaled_world_mercator(self):
        result = build_lut(make_mercator_filelist(), False, 9804)
        assert result[0].zoom == 1

    def test_build_lut_ellipsoidal_mercator(self):
        result = build_lut(make_mercator_filelist(), False, 3395)
        assert result[0].zoom == 1

    def test_build_lut_mercator(self):
        result = build_lut(make_mercator_filelist(), False, 3857)
        assert result[0].zoom == 1

    def test_build_lut_upper_left(self):
        result = build_lut(make_geodetic_filelist(), False, 4326)
        assert result[1].zoom == 2

    def test_build_lut_one(self):
        result = build_lut(make_geodetic_filelist(), True, 4326)
        assert result[1].zoom == 2

    def test_build_lut_two(self):
        result = build_lut(make_geodetic_filelist(), True, 4326)
        assert result[0].min_tile_col == 0

    def test_build_lut_three(self):
        result = build_lut(make_geodetic_filelist(), True, 4326)
        assert result[0].min_tile_row == 0

    def test_build_lut_four(self):
        result = build_lut(make_geodetic_filelist(), True, 4326)
        assert result[0].min_x == -180.0

    def test_build_lut_five(self):
        result = build_lut(make_geodetic_filelist(), True, 4326)
        assert result[0].min_y == -90.0

    def test_build_lut_six(self):
        result = build_lut(make_geodetic_filelist(), True, 4326)
        assert result[1].max_tile_row == 1

    def test_build_lut_seven(self):
        result = build_lut(make_geodetic_filelist(), True, 4326)
        assert result[1].max_tile_col == 1

    def test_build_lut_eight(self):
        result = build_lut(make_geodetic_filelist(), True, 4326)
        assert result[0].max_x == 0

    def test_build_lut_nine(self):
        result = build_lut(make_geodetic_filelist(), True, 4326)
        assert result[0].max_y == 90.0


class TestBuildLutNSG:

    def test_build_lut_nsg_length(self):
        result = build_lut_nsg(make_geodetic_filelist(), True, 4326, False)
        assert len(result) == 2

    def test_build_lut_nsg_min_max_row_col(self):
        result = build_lut_nsg(make_geodetic_filelist(), True, 4326, False)
        assert result[0].min_tile_row == 0
        assert result[0].max_tile_row == 4
        assert result[0].min_tile_col == 0
        assert result[0].max_tile_col == 2

        assert result[1].min_tile_row == 0
        assert result[1].max_tile_row == 8
        assert result[1].min_tile_col == 0
        assert result[1].max_tile_col == 4

    def test_build_lut_nsg_matrix_width_height(self):
        result = build_lut_nsg(make_geodetic_filelist(), True, 4326, False)
        assert result[0].matrix_width == 4
        assert result[0].matrix_height == 2

        assert result[1].matrix_width == 8
        assert result[1].matrix_height == 4


def test_combine_worker_dbs(make_session_folder):
    session_folder = make_session_folder
    # make a random number of tempdbs with dummy data
    img = new("RGB", (256, 256), "red")
    data = img_to_buf(img, 'jpeg').read()
    z = randint(2, 5)
    table_name = 'my tiles'
    for x in xrange(z):
        TempDB(join(gettempdir(), session_folder), table_name).insert_image_blob(x, 0, 0, Binary(data))
    # confirm that combine_worker_dbs assimilates all tempdb's into gpkg

    # necessary to put gpkg in session_folder
    gpkg = Geopackage(join(gettempdir(), session_folder, "test.gpkg"), 4326, table_name)
    gpkg.initialize()
    combine_worker_dbs(gpkg)
    result = gpkg.execute("select count(*) from '{table}';".format(table=table_name))
    assert (result.fetchone())[0] == z
    remove(gpkg.file_path)


# todo: test main
def test_main():
    table_name = "my_table"
    parser = argparse.ArgumentParser(description="convert tms folder into geopackage")
    parser.add_argument("source_folder", metavar="source")
    parser.add_argument("output_file", metavar="dest")
    parser.add_argument("-tileorigin", metavar="tile_origin", default="ll")
    parser.add_argument("-srs", metavar="srs", default=3857)
    parser.add_argument("-imagery", metavar="imagery", default="source")
    parser.add_argument("-q", metavar="quality", type=int, default=75)
    parser.add_argument("-t", dest="threading", action="store_false")
    parser.add_argument("-ogc", dest="nsg_profile")
    parser.add_argument("-renumber", default=False)
    parser.add_argument("-table_name", default=table_name)
    source = GEODETIC_FILE_PATH
    output_file = join(gettempdir(), uuid4().hex + ".gpkg")
    arg_list = parser.parse_args([source, output_file])
    main(arg_list)
    with get_database_connection(output_file) as db_conn:
        assert table_exists(cursor=db_conn.cursor(),
                            table_name=table_name)
    os.remove(output_file)


@pytest.fixture(scope="function")
def make_gpkg(tiles_table_name='tiles'):
    filename = uuid4().hex + '.gpkg'
    tmp_file = join(gettempdir(), filename)
    yield Geopackage(tmp_file, 4326, tiles_table_name)
    print ("deleting file")
    os.remove(tmp_file)


@pytest.fixture(scope="function")
def make_gpkg_nsg():
    filename = uuid4().hex + '.gpkg'
    tmp_file = join(gettempdir(), filename)
    yield NsgGeopackage(tmp_file, 4326, DEFAULT_TILES_TABLE_NAME)
    print ("deleting nsg file")
    os.remove(tmp_file)


def make_zmd():
    zmd = ZoomMetadata()
    zmd.zoom = 1
    zmd.min_tile_col = 1
    zmd.min_tile_row = 1
    zmd.min_x = 1
    zmd.min_y = 1
    zmd.max_tile_col = 2
    zmd.max_tile_row = 2
    zmd.max_x = 2
    zmd.max_y = 2
    zmd.matrix_width = 2
    zmd.matrix_height = 2
    return zmd


def make_zmd_list_geodetic():
    """Make a geodetic zoom level metadata mock object."""
    zmd_list = []
    for zoom in xrange(2, 6):
        zmd = ZoomMetadata()
        zmd.zoom = zoom
        zmd.min_tile_row = 0
        zmd.min_x = 0
        zmd.min_tile_col = 0
        zmd.min_y = 0
        zmd.max_tile_row = (2 ** (zoom - 1)) - 1
        zmd.max_x = zmd.max_tile_row
        zmd.max_tile_col = (2 ** zoom) - 1
        zmd.max_y = zmd.max_tile_col
        # zmd.matrix_width = (4 if zoom == 2 else zmd_list[zoom-3].matrix_width * 2)
        if zoom == 2:
            zmd.matrix_width = 4
        else:
            zmd.matrix_width = zmd_list[zoom - 3].matrix_width * 2
        # zmd.matrix_height = (2 if zoom == 2 else zmd_list[zoom-3].matrix_height * 2)
        if zoom == 2:
            zmd.matrix_height = 2
        else:
            zmd.matrix_height = zmd_list[zoom - 3].matrix_height * 2
        zmd_list.append(zmd)
    return zmd_list


def make_mercator_filelist():
    file_path = []
    for root, sub_folders, files in walk(MERCATOR_FILE_PATH):
        file_path += [join(root, f) for f in files if f.endswith('.png')]
    d1 = dict(x=0, y=0, z=1, path=file_path[0])
    d2 = dict(x=0, y=1, z=1, path=file_path[1])
    d3 = dict(x=1, y=0, z=1, path=file_path[2])
    d4 = dict(x=1, y=1, z=1, path=file_path[3])
    return [d1, d2, d3, d4]


def make_geodetic_filelist():
    file_path = []
    for root, sub_folders, files in walk(GEODETIC_FILE_PATH):
        file_path += [join(root, f) for f in files if f.endswith('.png')]
    d1 = dict(z=1, x=0, y=0, path=file_path[0])
    d2 = dict(z=2, x=0, y=0, path=file_path[1])
    d3 = dict(z=2, x=0, y=1, path=file_path[2])
    d4 = dict(z=2, x=1, y=0, path=file_path[3])
    d5 = dict(z=2, x=1, y=1, path=file_path[4])
    return [d1, d2, d3, d4, d5]


@pytest.fixture(scope="function")
def make_session_folder():
    session_folder = uuid4().hex
    mkdir(join(gettempdir(), session_folder))
    yield session_folder
    shutil.rmtree(join(gettempdir(), session_folder))
