#!/usr/bin/python
"""
Copyright (C) 2017 Reinventing Geospatial, Inc.

The MIT License (MIT)

Copyright (c) 2015 Reinventing Geospatial, Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Authors:
    Steven D. Lander
    Patricia Bui
Date: 2017-12
Description: Aux to GeoJson converter for raster cutlines

Caveats: This script assumes the source raster is in CRS84 or Global Geodetic
SRS.  The variable "jsonTemplate" is created in such a way as to assume that
SRS and others are not guaranteed to work (they probably won't).  If you come
across an aux file in a different SRS, you could possibly edit the
"crs:properties:name" to the desired SRS/CRS. This string would be found if you
mimicked the SRS in a generic geojson polygon made with QGIS or similar
products for the map product you are working with.

Version: 0.1
"""

from argparse import ArgumentParser
from collections import namedtuple

Point = namedtuple("Point", ["x", "y"])

jsonTemplate = """{{
    "crs": {{
        "properties": {{
            "name": "urn:ogc:def:crs:OGC:1.3:CRS84"
        }},
        "type": "name"
    }},
    "features": [
        {{
            "geometry": {{
                "coordinates": [
                    [
                        {:s}
                    ]
                ],
                "type": "Polygon"
            }},
            "properties": {{
                "id": 1
            }},
            "type": "Feature"
        }}
    ],
    "type": "FeatureCollection"
}}"""

def extract_bounds_from_aux(input_file):
    """
    Get the string of bounds from the input_file (aux.xml)
    """
    from xml.etree import ElementTree as ET
    from xml.etree.ElementTree import ParseError

    try:
        xml = ET.parse(input_file)
    except ParseError:
        print("Input file is not XML!")
        exit(1)
    root = xml.getroot()
    metadata = root.find("Metadata")    
    try:
        mdi_entries = metadata.findall("MDI")
        for mdi in mdi_entries:
            if mdi.get("key") == "Bounds":
                return mdi.text
        # This can happen if the tags used in the aux.xml
        # are not found
        print("Error: Invalid XML structure.")
        exit(1)
    except AttributeError:
        print("Error: Invalid XML structure.")
        exit(1)

def build_output_points(bounds):
    """
    Build a list of output points from the string bounds list
    """
    points = bounds.split(" ")
    # Build a list of Point tuples for easier parsing
    point_tuples = [Point(float(point.split(",")[0]), float(point.split(",")[1]))
            for point in points]

    # Set up our formatting entries
    format_template = "[{},{}]"
    normal_entry = format_template + ",\n\t\t\t"
    end_entry = format_template

    # Build the output string
    point_string = ""
    for point in point_tuples:
        point_string += normal_entry.format(point.x, point.y)
    point_string += end_entry.format(point_tuples[0].x, point_tuples[0].y)
    return point_string

def write_output_file(output, out_file):
    """
    Write output to out_file
    """
    with open(out_file, "a") as out:
        out.write(jsonTemplate.format(output))
    if exists(out_file):
        print("Output file " + out_file + " created!")
    else:
        print("Output file " + out_file + " not created correctly!")

def main(ARG_LIST):
    """
    Main
    """
    bounds = extract_bounds_from_aux(ARG_LIST.input_file)
    output = build_output_points(bounds)
    write_output_file(output, ARG_LIST.output_file)

if __name__ == "__main__":
    print("""
        aux2geojson.py  Copyright (C) 2017  Reinventing Geospatial, Inc
        This program comes with ABSOLUTELY NO WARRANTY.
        This is free software, and you are welcome to redistribute it
        under certain conditions.
    """)
    from os.path import exists

    PARSER = ArgumentParser("Convert aux.xml file to geojson boundary " +
            "for clipping")
    PARSER.add_argument("input_file",
            metavar="input_file",
            help="Input file to be converted to geojson")
    ARG_LIST = PARSER.parse_args()
    # Exit if no input file is specified
    if not exists(ARG_LIST.input_file):
        PARSER.print_usage()
        print("Input file specified does not exist.")
        exit(1)
    format_split = ARG_LIST.input_file.split(".")
    try:
        if format_split[-3] == "jp2" and format_split[-1] == "xml" \
                and format_split[-2] == "aux":
            # Typically this script should be pointed to <name>.jp2.aux.xml
            # files
            ARG_LIST.output_file = "".join(format_split[:-3]) + ".geojson"
        else:
            # But you could point it at a valid aux if the name isn't 
            # in that format
            print("WARNING: Input file should be a jp2.aux.xml file.")
            ARG_LIST.output_file = ARG_LIST.input_file + ".geojson"
    except IndexError:
        # Also can handle cases there the file name is really short
        print("WARNING: Input file should be a jp2.aux.xml file.")
        ARG_LIST.output_file = ARG_LIST.input_file + ".geojson"
    main(ARG_LIST)
