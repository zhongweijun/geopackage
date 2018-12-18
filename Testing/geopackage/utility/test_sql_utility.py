from pytest import raises

from Testing.test_tiles2gpkg import make_gpkg
from scripts.geopackage.core.geopackage_core import GeoPackageCore, GEOPACKAGE_CONTENTS_TABLE_NAME
from scripts.geopackage.extensions.extension import Extension, EXTENSION_READ_WRITE_SCOPE
from scripts.geopackage.extensions.geopackage_extensions import GeoPackageExtensions, GEOPACKAGE_EXTENSIONS_TABLE_NAME
from scripts.geopackage.utility.sql_column_query import SqlColumnQuery
from scripts.geopackage.utility.sql_utility import get_database_connection, column_exists, row_id_exists, select_query, \
    update_row, insert_row


class TestSqlUtility(object):

    def test_column_doesnt_exist(self, make_gpkg):
        gpkg = make_gpkg

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()
            GeoPackageCore.create_core_tables(cursor=cursor)
            assert not column_exists(cursor=cursor,
                                     table_name=GEOPACKAGE_CONTENTS_TABLE_NAME,
                                     column_name="not_in_gpkg_contents")

    def test_column_doesnt_exist_2(self, make_gpkg):
        gpkg = make_gpkg

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()
            assert not column_exists(cursor=cursor,
                                     table_name=GEOPACKAGE_CONTENTS_TABLE_NAME,
                                     column_name="not_in_gpkg_contents")

    def test_row_id_doesnt_exist(self, make_gpkg):
        gpkg = make_gpkg

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()
            assert not row_id_exists(cursor=cursor,
                                     table_name=GEOPACKAGE_CONTENTS_TABLE_NAME,
                                     row_id=1)

    def test_select_query_returns_no_rows(self, make_gpkg):
        gpkg = make_gpkg
        gpkg.initialize()

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()
            rows = select_query(cursor=cursor,
                                table_name=GEOPACKAGE_CONTENTS_TABLE_NAME,
                                select_columns=['table_name', 'data_type', 'srs_id'],
                                where_columns_dictionary={'table_name': 'I dont exist'})

            assert len(rows) == 0

    def test_select_query_raises_error(self, make_gpkg):
        gpkg = make_gpkg

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()
            with raises(ValueError):
                select_query(cursor=cursor,
                             table_name='I dont exist',
                             select_columns=['table', 'stuff'],
                             where_columns_dictionary={'table': True, 'stuff': 1.0})

    def test_select_query_invalid_column_names_none(self, make_gpkg):
        gpkg = make_gpkg
        gpkg.initialize()
        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()
            with raises(ValueError):
                select_query(cursor=cursor,
                             table_name=GEOPACKAGE_CONTENTS_TABLE_NAME,
                             select_columns=['table', None],  # invalid
                             where_columns_dictionary={'table': True, 'stuff': 1.0})

    def test_select_query_invalid_column_names_empty(self, make_gpkg):
        gpkg = make_gpkg
        gpkg.initialize()
        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()
            with raises(ValueError):
                select_query(cursor=cursor,
                             table_name=GEOPACKAGE_CONTENTS_TABLE_NAME,
                             select_columns=['table', ''],  # invalid
                             where_columns_dictionary={'table': True, 'stuff': 1.0})

    def test_update_row(self, make_gpkg):
        gpkg = make_gpkg

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()

            GeoPackageExtensions.create_extensions_table(cursor=cursor)
            existing_extension = Extension(table_name=None,
                                           column_name=None,
                                           extension_name='my_extension',
                                           definition='definition1',
                                           scope=EXTENSION_READ_WRITE_SCOPE)

            GeoPackageExtensions.insert_or_update_extensions_row(cursor=cursor,
                                                                 extension=existing_extension)

            # check that the extension row was added
            rows = select_query(cursor=cursor,
                                table_name=GEOPACKAGE_EXTENSIONS_TABLE_NAME,
                                select_columns=['table_name'],
                                where_columns_dictionary={'table_name': existing_extension.table_name,
                                                          'column_name': existing_extension.column_name,
                                                          'extension_name': existing_extension.extension_name,
                                                          'definition': existing_extension.definition,
                                                          'scope': existing_extension.scope})
            assert rows is not None and len(rows) == 1

            # try to add the same extension twice, but update the definition value
            existing_extension.definition = 'updated definition'

            GeoPackageExtensions.insert_or_update_extensions_row(cursor=cursor,
                                                                 extension=existing_extension)

            # check that the extension row was only updated and not added
            rows = select_query(cursor=cursor,
                                table_name=GEOPACKAGE_EXTENSIONS_TABLE_NAME,
                                select_columns=['definition'],
                                where_columns_dictionary={'table_name': existing_extension.table_name,
                                                          'column_name': existing_extension.column_name,
                                                          'extension_name': existing_extension.extension_name})
            assert rows is not None and len(rows) == 1
            # check to make sure the row's definition column was updated
            assert rows[0]['definition'] == existing_extension.definition

    def test_update_row_no_table(self, make_gpkg):
        gpkg = make_gpkg

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()
            with raises(ValueError):
                update_row(cursor=cursor,
                           table_name='not existant',  # doesn't exist
                           set_columns_dictionary={'column1': None},
                           where_columns_dictionary={'column1': None})

    def test_update_row_invalid_column_names_empty(self, make_gpkg):
        gpkg = make_gpkg
        gpkg.initialize()

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()
            with raises(ValueError):
                update_row(cursor=cursor,
                           table_name=GEOPACKAGE_CONTENTS_TABLE_NAME,
                           set_columns_dictionary={'': None},
                           where_columns_dictionary={'column1': None})

    def test_insert_row_no_table(self, make_gpkg):
        gpkg = make_gpkg

        with get_database_connection(gpkg.file_path) as db_conn:
            cursor = db_conn.cursor()
            with raises(ValueError):
                insert_row(cursor=cursor,
                           table_name='not existant',  # doesn't exist
                           sql_columns_list=[SqlColumnQuery(column_name='column',
                                                            column_value=None)])
