from lib.sql_cmds import *
import unittest


# Test the DB connection
class TestDBConnection(unittest.TestCase):
    def test_connection(self):
        with connect("127.0.0.1", "root", "your_root_password") as conn:
            self.assertIsNotNone(conn, "!! CONNECTION FAILED !!")
            dbs = list_databases(conn)


class TestDB(unittest.TestCase):
    def test_table_create(self):
        with connect("127.0.0.1", "root", "your_root_password") as conn:
            create_database(conn, "test_db")
            columns_list = [("id", "INT"), ("name", "VARCHAR(255)"),
                            ("age", "INT")]
            add_table(conn, "test_db", "test_table",
                      columns_list)
            cols = get_table_columns(conn, "test_table")
            self.assertIsNotNone(cols, "!! TABLE CREATE FAILED !!")
            drop_table(conn, "test_table")
            drop_database(conn, "test_db")


class TestDBInsert(unittest.TestCase):
    def test_insert_into_table(self):
        with connect("127.0.0.1", "root", "your_root_password") as conn:
            create_database(conn, "test_db")
            columns_list = [("id", "INT"), ("name", "VARCHAR(255)"),
                            ("age", "INT")]
            add_table(conn, "test_db", "test_table",
                      columns_list)
            insert(conn, "test_table", ["id", "name", "age"],
                              [1, "John", 20])
            q = execute_query(conn, "SELECT * FROM test_table")
            self.assertIs(q[0][0], 1, "!! INSERT INTO TABLE FAILED !!")
            drop_table(conn, "test_table")
            drop_database(conn, "test_db")


if __name__ == "__main__":
    unittest.main(verbosity=2)
