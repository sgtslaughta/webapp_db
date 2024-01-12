import mysql.connector
import logging

logging.basicConfig(filename='log/sql_cmds.log', level=logging.DEBUG,
                    format='%(asctime)s:%(levelname)s:%(message)s')

def connect():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="your_user",
            password="your_password")
        return conn
    except mysql.connector.errors.ProgrammingError:
        print("Invalid username or password")
        logging.error("Invalid username or password")
        return None
    except mysql.connector.errors.InterfaceError:
        print("Invalid host")
        return None


def create_database(conn, database_name):
    try:
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE {database_name}")
        cursor.close()
    except mysql.connector.errors.DatabaseError:
        print(f"Database {database_name} already exists")
    finally:
        conn.close()


def add_table(conn, table_name, columns):
    try:
        cursor = conn.cursor()
        cursor.execute(f"CREATE TABLE {table_name} ({columns})")
        cursor.close()
    except mysql.connector.errors.DatabaseError:
        print(f"Table {table_name} already exists")
    finally:
        conn.close()


def insert(conn, table_name, columns, values):
    try:
        cursor = conn.cursor()
        cursor.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({values})")
        cursor.close()
    except mysql.connector.errors.DatabaseError:
        print(f"Table {table_name} already exists")
    finally:
        conn.close()


def execute_query(connection, query):
    cursor = None
    try:
        # Create a cursor object
        cursor = connection.cursor()
        # Execute the query
        cursor.execute(query)
        # Fetch all the rows (results)
        result = cursor.fetchall()
        return result
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        # Close the cursor (connection will be closed separately)
        if 'cursor' in locals() and cursor is not None:
            cursor.close()


def update(conn, table_name, columns, where_clause):
    try:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE {table_name} SET {columns} WHERE {where_clause}")
        cursor.close()
    except mysql.connector.errors.DatabaseError:
        print(f"Table {table_name} already exists")
    finally:
        conn.close()


def delete(conn, table_name, where_clause):
    try:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {table_name} WHERE {where_clause}")
        cursor.close()
    except mysql.connector.errors.DatabaseError:
        print(f"Table {table_name} already exists")
    finally:
        conn.close()

