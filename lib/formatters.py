import pandas as pd
from lib.sql_cmds import *
from datetime import datetime


def table_data_to_df(conn, db_name, table_name):
    """Convert table data to pandas dataframe"""
    data = get_table_data(conn, db_name, table_name)
    df = pd.DataFrame(data)
    return df


def send_approvals_to_server(approved_items, user):
    with connect(HOST, PORT, USER, PASSWORD) as conn:
        if conn:
            uid = get_user_id_from_name(conn, "webapp_db", "users", user)
            try:
                if uid["user_id"]:
                    uid = uid["user_id"]
                else:
                    return False
            except TypeError as e:
                print(e)
                return False
            col_vals = "approval_status = 'approved', date_approved = NOW(), " \
                       f"id_approved_by = {uid}"
            for i in [*approved_items["request_id"]]:
                set_row_value(conn, "webapp_db", "requests",
                              col_vals,
                              f"request_id = {i}")
            return True
        return False


def update_users_last_active(user_name):
    """Update the last active time for the user"""
    with connect(HOST, PORT, USER, PASSWORD) as conn:
        if conn:
            uid = get_user_id_from_name(conn, "webapp_db", "users", user_name)
            try:
                if uid["user_id"]:
                    uid = uid["user_id"]
                else:
                    return False
            except TypeError as e:
                print(e)
                return False
            current_datetime = datetime.now()
            formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
            col_vals = f"date_last_active = '{formatted_datetime}'"
            condition = f"user_id = '{uid}'"
            set_row_value(conn, "webapp_db", "users", col_vals, condition)
            return True
        return False


def item_to_xml(xml_type, item):
    """Convert email to XML"""
    return f"<{xml_type}>{item}</{xml_type}>"


def add_user_to_db(user_name):
    """Add new user to the database"""
    with connect(HOST, PORT, USER, PASSWORD) as conn:
        if conn:
            # Check to see if user already exists
            user_id = get_user_id_from_name(conn, "webapp_db", "users",
                                            user_name)
            try:
                if user_id["user_id"]:
                    return False
            except TypeError:
                pass
            vals = {"user_name": user_name}
            add_entry_to_table(conn, "webapp_db", "users", vals)
            update_users_last_active(user_name)
            return True
        return False


def get_requests_by_user(user_name):
    """Get requests by user"""
    with connect(HOST, PORT, USER, PASSWORD) as conn:
        if conn:
            uid = get_user_id_from_name(conn, "webapp_db", "users", user_name)
            try:
                if uid["user_id"]:
                    uid = uid["user_id"]
                else:
                    return None
            except TypeError:
                pass
            selected_columns = ["request_id", "date_created", "approval_status",
                                "date_approved", "xml_text"]

            query = (f"SELECT {', '.join(selected_columns)} FROM "
                     f"webapp_db.requests WHERE id_created_by = '{uid}'")
            data = execute_query(conn, query)
            return data
        return None


def remove_user_request_by_id(request_id):
    """Remove user request by ID"""
    with connect(HOST, PORT, USER, PASSWORD) as conn:
        if conn:
            remove_entry_from_table(conn, "webapp_db", "requests",
                                    f"request_id = '{request_id}'")
            return True
        return False


def capture_private_keys_and_other_lines(text):
    lines = text.splitlines()
    private_keys = []
    other_lines = []

    is_private_key = False
    current_key = ""

    for line in lines:
        if "-----BEGIN OPENSSH PRIVATE KEY-----" in line:
            # Found the start marker of a private key
            is_private_key = True
            current_key += line + "\n"
        elif "-----END OPENSSH PRIVATE KEY-----" in line:
            # Found the end marker of a private key
            is_private_key = False
            current_key += line + "\n"
            private_keys.append(current_key)
            current_key = ""
        elif is_private_key:
            # Continue adding lines to the current private key
            current_key += line + "\n"
        else:
            # Non-private key line
            other_lines.append(line)

    return private_keys, other_lines