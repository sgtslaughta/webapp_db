from lib.sql_cmds import *

request_table_create = """
USE webapp_db;
CREATE TABLE `requests` (
	`request_id` BIGINT NOT NULL AUTO_INCREMENT,
	`date_created` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 
	'Date request was created',
	`id_created_by` INT DEFAULT NULL,  -- Set the default value to NULL
	`approval_status` ENUM('pending', 'approved', 'rejected') NOT NULL 
	DEFAULT 'pending',
	`date_approved` TIMESTAMP DEFAULT NULL,
	`id_approved_by` INT DEFAULT NULL,
	`xml_text` LONGTEXT NOT NULL,
	KEY `request_index` (`request_id`) USING BTREE,
	PRIMARY KEY (`request_id`),
	FOREIGN KEY (`id_created_by`) REFERENCES `user` (`id`),
	FOREIGN KEY (`id_approved_by`) REFERENCES `user` (`id`),
	INDEX `id_created_by` (`id_created_by`),
	INDEX `id_approved_by` (`id_approved_by`)
);
"""

user_table_create = """
USE webapp_db;
CREATE TABLE `users` (
	`user_id` INT NOT NULL AUTO_INCREMENT COMMENT 'User ID',
	`user_name` VARCHAR(255),
	`date_user_created` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	`date_last_active` TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (`user_id`)
);
"""


# Function to create columns list for 'users' table
def get_users_columns():
    return [
        ("user_id", "INT NOT NULL AUTO_INCREMENT COMMENT 'User ID'"),
        ("user_name", "VARCHAR(255)"),
        ("date_user_created", "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP"),
        ("date_last_active", "TIMESTAMP"),
    ]


# Function to create columns list for 'requests' table
def get_requests_columns():
    return [
        ("request_id", "BIGINT NOT NULL AUTO_INCREMENT"),
        ("date_created",
         "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Date request was created'"),
        ("id_created_by", "INT DEFAULT NULL"),
        ("approval_status",
         "ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending'"),
        ("date_approved", "TIMESTAMP DEFAULT NULL"),
        ("id_approved_by", "INT DEFAULT NULL"),
        ("xml_text", "LONGTEXT NOT NULL"),
    ]


# Function to create keys list for 'users' table
def get_users_keys():
    return [
        "PRIMARY KEY (user_id)"
    ]


# Function to create keys list for 'requests' table
def get_requests_keys():
    return [
        "PRIMARY KEY (request_id)",
        "KEY request_index (request_id) USING BTREE",
        "INDEX id_created_by (id_created_by)",
        "INDEX id_approved_by (id_approved_by)"
    ]


def table_exists(conn, db_name, table_name):
    """
    Check if a table exists in the specified database.
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"USE {db_name}")
            cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
            return cursor.fetchone() is not None
    except Exception as e:
        print(f"Error checking table existence: {e}")
        logging.error(f"Error checking table existence: {e}")
        return False


def init_db():
    try:
        with connect("127.0.0.1", 3306, "root",
                     "ASuperStrongAndSecurePassword123!!!") as conn:
            if conn:
                # Add 'users' table if it doesn't exist
                if not table_exists(conn, "webapp_db", "users"):
                    add_table(conn, "webapp_db", "users", get_users_columns(),
                              get_users_keys(), create_query=None)

                # Add 'requests' table if it doesn't exist
                if not table_exists(conn, "webapp_db", "requests"):
                    add_table(conn, "webapp_db", "requests",
                              get_requests_columns(), get_requests_keys(),
                              create_query=None)

                print("User and request tables created successfully.")
                logging.info("DB init successful.")
    except Exception as err:
        print(f"Error: {err}. See logs...")
        logging.error(f"Error creating database 'webapp_db': {err}")


if __name__ == "__main__":
    init_db()
