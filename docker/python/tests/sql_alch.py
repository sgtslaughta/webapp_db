import sqlalchemy as sq
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import (Mapped, mapped_column, MappedAsDataclass,
                            DeclarativeBase)
import json
from os import environ
import logging

# db_username = environ.get("DB_USERNAME")
# db_password = environ.get("DB_PASSWORD")
# db_hostname = environ.get("DB_HOSTNAME")
# db_database = environ.get("DB_DATABASE")

db_username = 'root'
db_password = 'ASuperStrongAndSecurePassword123!!!'
db_hostname = 'localhost'
db_database = 'webapp_db'


def init_engine(echo=False):
    try:
        return sq.create_engine(f"mysql+mysqlconnector://{db_username}"
                                f":{db_password}@{db_hostname}/{db_database}",
                                echo=echo)
    except Exception as e:
        logging.error(f"Error creating engine: {e}")

# with engine.connect() as conn:
#     # name = "NEWNAME"
#     # stmt = sq.text(f"UPDATE users SET user_name = :name WHERE user_id = 1")
#     # conn.execute(stmt, {"name": name})
#     stmt = sq.text("SELECT * FROM users")
#     result = conn.execute(stmt).all()
#     conn.commit()


class Base(MappedAsDataclass, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, init=False, autoincrement=True)
    user_name: Mapped[str] = sq.Column(sq.String(50), unique=True, nullable=False)
    date_user_created: Mapped[datetime] = mapped_column(init=False, server_default=sq.func.now())
    date_last_active: Mapped[datetime] = sq.Column(sq.TIMESTAMP, server_default=sq.func.now(),
                                                    onupdate=sq.func.now())


class Request(Base):
    __tablename__ = "requests"
    id: Mapped[int] = mapped_column(primary_key=True, init=False,
                                    index=True, autoincrement=True)
    date_created: Mapped[datetime] = mapped_column(init=False, server_default=sq.func.now())
    id_created_by: Mapped[int] = mapped_column(sq.ForeignKey(
        "users.id"),
                                            index=True)
    approval_status: Mapped[str] = sq.Column(sq.Enum("pending", "approved", "rejected"),
                                            server_default="pending")
    date_approved: Mapped[Optional[datetime]] = sq.Column(sq.TIMESTAMP)
    id_approved_by: Mapped[Optional[int]] = sq.Column(sq.ForeignKey(
        "users.id"))
    request_data: Mapped[str] = sq.Column('data', sq.JSON)


# with engine.begin() as conn:
#     Base.metadata.create_all(conn)
#     # List the tables in the database
#     stmt = sq.text("SHOW TABLES")
#     result = conn.execute(stmt).all()
#     print(result)


def init_create_tables(engine):
    try:
        with engine.connect() as conn:
            Base.metadata.create_all(conn)
            return True
    except Exception as e:
        print(f"Error creating tables: {e}")
        return False


def get_table(engine, table_name):
    try:
        with engine.connect() as conn:
            return conn.execute(sq.text(f"SELECT * FROM {table_name}")).all()
    except Exception as e:
        print(f"Error getting {table_name}: {e}")
        return None


def test_if_user_exists(engine, table, user_name):
    try:
        with engine.connect() as conn:
            stmt = sq.text(f"SELECT * FROM {table} WHERE user_name = :user_name")
            result = conn.execute(stmt, {"user_name": user_name}).all()
            return len(result) > 0
    except Exception as e:
        print(f"Error checking if {user_name} exists: {e}")
        return False


def update_row_by_id(engine, table, uid, column, value):
    with engine.connect() as conn:
        stmt = sq.text(f"UPDATE {table} SET {column} = :value WHERE id = :id")
        conn.execute(stmt, {"value": value, "id": uid})
        conn.commit()


def remove_item_by_id(engine, table, uid):
    try:
        with engine.connect() as conn:
            stmt = sq.text(f"DELETE FROM {table} WHERE user_id = :id")
            conn.execute(stmt, {"id": uid})
            conn.commit()
            return True
    except Exception as e:
        print(f"Error removing item:{uid} from {table}: {e}")
        return False


def get_row_by_id(engine, table, uid):
    try:
        with engine.connect() as conn:
            stmt = sq.text(f"SELECT * FROM {table} WHERE id = :id")
            result = conn.execute(stmt, {"id": uid}).all()
            return result
    except Exception as e:
        print(f"Error getting row:{uid} from {table}: {e}")
        return None


def get_username_by_id(engine, table, uid):
    try:
        with engine.connect() as conn:
            stmt = sq.text(f"SELECT user_name FROM {table} WHERE id = :id")
            result = conn.execute(stmt, {"id": uid}).all()
            return result[0][0]
    except Exception as e:
        print(f"Error getting username from {table}: {e}")
        return None


def add_item_to_table(engine, table_class, **kwargs):
    try:
        insert_statement = sq.Insert(table_class)
        insert_statement = insert_statement.values(**kwargs)
        with engine.begin() as conn:
            conn.execute(insert_statement)
            return True
    except Exception as e:
        print(f"Error adding item to {table_class}: {e}")
        return False


def get_tables(engine):
    try:
        with engine.connect() as conn:
            stmt = sq.text("SHOW TABLES")
            result = conn.execute(stmt).all()
            return result
    except Exception as e:
        print(f"Error getting tables: {e}")
        return None


def run_query(engine, query):
    try:
        with engine.connect() as conn:
            stmt = sq.text(query)
            result = conn.execute(stmt).all()
            return result
    except Exception as e:
        print(f"Error running query: {e}")
        return None


def get_schema(engine, table):
    try:
        with engine.connect() as conn:
            stmt = sq.text(f"SHOW COLUMNS FROM {table}")
            result = conn.execute(stmt).all()
            return result
    except Exception as e:
        print(f"Error getting schema for {table}: {e}")
        return None


e = init_engine()
# for i in range(1, 11):
#     add_item_to_table(e, Request, id_created_by=i, data=json.dumps({"test":
#                                                                        "test"}))
x = sq.select(User.user_name, Request.request_data).join_from(Request,
                                                              User, onclause=User.id == Request.id_created_by)
with e.connect() as conn:
    result = conn.execute(x).all()
    for i in result:
        print(i)
# stmnt2 = sq.select(Request)
# with e.connect() as conn:
#     result = conn.execute(stmnt2).all()
#     print(result)
# print(get_schema(e, "requests"))
# print(get_table(e, "requests"))
# if add_item_to_table(e, Request, id_created_by=1, data=json.dumps({"test":
#                                                                        "test"})):
#     print("Added request")
# print(get_table(e, "requests"))


