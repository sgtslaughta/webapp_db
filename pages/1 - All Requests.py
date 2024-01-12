import streamlit as st
from lib.formatters import *
import logging

logging.basicConfig(level=logging.WARNING)


def fetch_data():
    with connect("127.0.0.1", 3306, "root",
                 "ASuperStrongAndSecurePassword123!!!") as conn:
        if conn:
            return table_data_to_df(conn, "webapp_db", "requests")


def set_data():
    st.session_state.fetched_data = fetch_data()


def dataframe_with_selections(df):
    df_with_selections = df.copy()
    df_with_selections.insert(0, "Select", False)

    # Get dataframe row-selections from user with st.data_editor
    edited_df = st.data_editor(
        df_with_selections,
        hide_index=True,
        column_config={"Select": st.column_config.CheckboxColumn(required=True)},
        disabled=df.columns,
    )

    # Filter the dataframe using the temporary column, then drop the column
    selected_rows = edited_df[edited_df.Select]
    return selected_rows.drop('Select', axis=1)


def print_selected_rows(rows):
    st.write(rows[["request_id", "approval_status"]])


st.title("All Requests")

st.write("This is the 'All Requests' page")
if "fetched_data" not in st.session_state:
    set_data()

selection = dataframe_with_selections(st.session_state.fetched_data)

approve = st.button("Approve", on_click=print_selected_rows, args=[selection])
st.button("Refresh Data", on_click=set_data)
