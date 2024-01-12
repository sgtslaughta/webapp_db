import pandas as pd
from lib.sql_cmds import *


def table_data_to_df(conn, db_name, table_name):
    """Convert table data to pandas dataframe"""
    data = get_table_data(conn, db_name, table_name)
    df = pd.DataFrame(data)
    return df
