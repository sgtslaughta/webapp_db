import mysql.connector
import logging
from logging.handlers import RotatingFileHandler
import re
from contextlib import contextmanager
import os

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
logs_folder_path = current_dir.replace('lib', 'logs')
# Ensure the 'logs' folder exists
os.makedirs(logs_folder_path, exist_ok=True)
# Set the root logger to log to a default file (if needed)
log_filename = os.path.join(logs_folder_path, 'app.log')
logging.basicConfig(filename=log_filename, level=logging.DEBUG,
                    format='%(asctime)s:%(levelname)s:%(message)s')
# Create a custom logger for SQL-related functions
sql_logger = logging.getLogger('sql_logger')
sql_logger.setLevel(logging.DEBUG)
# Configure a RotatingFileHandler for SQL-related logs
sql_log_filename = os.path.join(logs_folder_path, 'SQL.log')
sql_handler = RotatingFileHandler(sql_log_filename, maxBytes=1000000, backupCount=5)
sql_handler.setLevel(logging.DEBUG)
# Define a formatter for the SQL logs
sql_formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
sql_handler.setFormatter(sql_formatter)
# Attach the handler to the SQL logger
sql_logger.addHandler(sql_handler)
sql_logger.propagate = False
sql_logger.debug("Logger initialized")

maria_db_data_types = [
    'TINYINT',
    'SMALLINT',
    'MEDIUMINT',
    'INT',
    'INTEGER',
    'BIGINT',
    'DECIMAL',
    'FLOAT',
    'DOUBLE',
    'DATE',
    'TIME',
    'DATETIME',
    'TIMESTAMP',
    'YEAR',
    'CHAR',
    'VARCHAR',
    'TINYTEXT',
    'TEXT',
    'MEDIUMTEXT',
    'LONGTEXT',
    'BINARY',
    'VARBINARY',
    'TINYBLOB',
    'BLOB',
    'MEDIUMBLOB',
    'LONGBLOB',
    'ENUM',
    'SET',
    'BINARY',
    'VARBINARY',
    'TINYBLOB',
    'BLOB',
    'MEDIUMBLOB',
    'LONGBLOB',
    'GEOMETRY',
    'POINT',
    'LINESTRING',
    'POLYGON',
    'MULTIPOINT',
    'MULTILINESTRING',
    'MULTIPOLYGON',
    'GEOMETRYCOLLECTION',
    'JSON',
    'BIT',  # MariaDB extension
    'BOOL',  # MariaDB extension
    'BOOLEAN',  # MariaDB extension
    'SET',
    'ENUM',
    'SEQUENCE'  # MariaDB extension
]


def sanitize_name(name):
    try:
        invalid_chars_pattern = re.compile(r"[^a-zA-Z0-9_]+")
        sanitized_name = re.sub(invalid_chars_pattern, "_", name)
        sql_logger.debug(f"Sanitized name: {name} -> {sanitized_name}")
        return sanitized_name
    except Exception as e:
        sql_logger.error(f"Error in sanitize_name: {e}")
        return None


@contextmanager
def connect(host, user, password):
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password
        )
        sql_logger.debug("Connection established successfully")
        yield connection
    except mysql.connector.errors.ProgrammingError as pe:
        print("Invalid username or password")
        sql_logger.error(f"Invalid username or password: {pe}")
    except mysql.connector.errors.InterfaceError as ie:
        print("Invalid host")
        sql_logger.error(f"Invalid host: {ie}")
    finally:
        if connection is not None:
            connection.close()


def list_databases(conn):
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES")
        databases = cursor.fetchall()
        return databases
    except mysql.connector.errors.DatabaseError:
        print("Invalid database")
        return None


def list_tables(conn, database_name):
    try:
        cursor = conn.cursor()
        cursor.execute(f"SHOW TABLES FROM {database_name}")
        tables = cursor.fetchall()
        sql_logger.debug(f"List of tables in database {database_name}: {tables}")
        return tables
    except mysql.connector.errors.DatabaseError:
        print("Invalid database")
        sql_logger.error("Invalid database")
        return None


def get_table_columns(conn, table_name):
    try:
        cursor = conn.cursor()
        cursor.execute(f"SHOW COLUMNS FROM {table_name}")
        columns = cursor.fetchall()
        sql_logger.debug(f"Columns of table {table_name}: {columns}")
        return columns
    except mysql.connector.errors.DatabaseError:
        print("Invalid database")
        sql_logger.error("Invalid database")
        return None


def create_database(connection, db_name):
    cursor = None
    db_name = sanitize_name(db_name)
    try:
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        sql_logger.debug(f"Database '{db_name}' created successfully")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        sql_logger.error(f"Error creating database '{db_name}': {err}")
    finally:
        if cursor is not None:
            cursor.close()


def make_column(column_name, data_type, primary_key=False, auto_increment=True,
                nullable="YES"):
    column = f"{column_name} {data_type} {nullable} "
    if data_type not in maria_db_data_types:
        sql_logger.error(f"Invalid data type: {data_type}")
        return None
    if primary_key:
        column += " COLUMN_KEY"
    if auto_increment:
        column += " AUTO_INCREMENT"
    return column


def add_table(conn, db, table_name, columns):
    table_name = sanitize_name(table_name)
    try:
        cursor = conn.cursor()
        cursor.execute(f"USE {db}")
        # Generate the column definition for the CREATE TABLE statement
        columns_sql = ", ".join(
            [f"{name} {data_type}" for name, data_type in columns])
        cursor.execute(f"CREATE TABLE {table_name} ({columns_sql})")
        sql_logger.debug(
            f"Table '{table_name}' created successfully in database '{db}'")
    except mysql.connector.errors.DatabaseError as e:
        print(f"Table {table_name} already exists: {e}")
        sql_logger.error(
            f"Error creating table '{table_name}' in database '{db}': {e}")


def drop_database(conn, database_name):
    try:
        cursor = conn.cursor()
        cursor.execute(f"DROP DATABASE {database_name}")
        sql_logger.debug(f"Database '{database_name}' dropped successfully")
    except mysql.connector.errors.DatabaseError as e:
        print(f"Database {database_name} does not exist: {e}")
        sql_logger.error(
            f"Error dropping database '{database_name}': Database does not exist")


def drop_table(conn, table_name):
    try:
        cursor = conn.cursor()
        cursor.execute(f"DROP TABLE {table_name}")
        sql_logger.debug(f"Table '{table_name}' dropped successfully")
    except mysql.connector.errors.DatabaseError:
        print(f"Table {table_name} does not exist")
        sql_logger.error(
            f"Error dropping table '{table_name}': Table does not exist")


def insert(conn, table_name, columns, values):
    try:
        cursor = conn.cursor()
        columns = ", ".join(columns)
        values = ", ".join([f"'{value}'" for value in values])
        cursor.execute(
            f"INSERT INTO {table_name} ({columns}) VALUES ({values})")
        sql_logger.debug(f"Data inserted into table '{table_name}' successfully")
    except mysql.connector.errors.DatabaseError as e:
        print(f"Table {table_name} already exists: ", e)
        sql_logger.error(
            f"Error inserting data into table '{table_name}': {e}")


def execute_query(connection, query):
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        sql_logger.debug(f"Query executed successfully: {query}")
        return result
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        sql_logger.error(f"Error executing query: {err}")


def update(conn, table_name, columns, where_clause):
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE {table_name} SET {columns} WHERE {where_clause}")
        sql_logger.debug(f"Data in table '{table_name}' updated successfully")
    except mysql.connector.errors.DatabaseError:
        print(f"Table {table_name} already exists")
        sql_logger.error(
            f"Error updating data in table '{table_name}': Table does not exist")


def delete(conn, table_name, where_clause):
    try:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {table_name} WHERE {where_clause}")
        sql_logger.debug(f"Data in table '{table_name}' deleted successfully")
    except mysql.connector.errors.DatabaseError:
        print(f"Table {table_name} already exists")
        sql_logger.error(
            f"Error deleting data in table '{table_name}': Table does not exist")
