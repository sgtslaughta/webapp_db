from lib.sql_cmds import *


def add_new_user(conn, user_name):
    """Add new user to the database"""
    vals = {"user_name": user_name}
    add_entry_to_table(conn, "webapp_db", "users", vals)
    data = get_table_data(conn, "webapp_db", "users")
    for row in data:
        print(row)


def add_new_request(conn, xml_text):
    """Add new request to the database"""
    vals = {"xml_text": xml_text,
            "id_created_by": 10}
    add_entry_to_table(conn, "webapp_db", "requests", vals)
    data = get_table_data(conn, "webapp_db", "requests")
    for row in data:
        print(row)


def remove_user(conn, condition):
    """Delete user from the database"""
    remove_entry_from_table(conn, "webapp_db", "users", condition)
    data = get_table_data(conn, "webapp_db", "users")
    for row in data:
        print(row)


with connect("127.0.0.1", 3306, "root",
                     "ASuperStrongAndSecurePassword123!!!") as conn:
    if conn:
        add_new_user(conn, "new_user2")
        xml_text = """
        <request>
            <request_id>1</request_id>
            <date_created>2020-01-01 00:00:00</date_created>
            <id_created_by>1</id_created_by>werwer
            <approval_status>pending</approval_status>
            <date_approved>2020-01-01 00:00:00</date_approved>
            <id_approved_by>1</id_approved_by>
            <xml_text>xml_text</xml_text>
        </request>
        """
        add_new_request(conn, xml_text)
        condition = "user_name LIKE 'new_user2'"
        remove_user(conn, condition)

