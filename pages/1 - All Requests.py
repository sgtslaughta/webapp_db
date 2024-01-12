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
    st.sidebar.success("Data refreshed")


def dataframe_with_selections(df):
    df_with_selections = df.copy()
    df_with_selections.insert(0, "Select", False)

    # Get dataframe row-selections from user with st.data_editor
    edited_df = st.data_editor(
        df_with_selections,
        hide_index=True,
        column_config={
            "Select": st.column_config.CheckboxColumn(required=True)},
        disabled=df.columns,
    )

    # Filter the dataframe using the temporary column, then drop the column
    selected_rows = edited_df[edited_df.Select]
    return selected_rows.drop('Select', axis=1)


def print_selected_rows(rows):
    if "submissions" not in st.session_state:
        st.session_state.submissions = []
    st.session_state.submissions = rows

def submit():
    st.sidebar.success("Rows submitted for approval")
    st.balloons()
    # deselect rows
    set_data()


st.title("All Requests")

st.write("This is the 'All Requests' page")
if "fetched_data" not in st.session_state:
    set_data()

col1, col2, col3, col4, col5 = st.columns(5, gap="small")
with col5:
    st.button("🔄", on_click=set_data, help="Refresh data")

selection = dataframe_with_selections(st.session_state.fetched_data)

st.write("INFO: To view the request XML, scroll to the right inside the data"
         " table. Then double click the cell containing the XML text.")
approve_txt = "Select as many items as you wish to approve, then click the " \
              "button below to approve and submit your selections for " \
              "processing. This action cannot be undone and will be " \
              "executed immediately."
approve = st.button("Approve & Submit", on_click=print_selected_rows,
                    args=[selection], type="primary", help=approve_txt)
if approve:
    with st.container(border=True):
        st.write("The following rows will be submitted for approval:")
        st.write(st.session_state.submissions)
        st.session_state.submissions = []
        col1, col2 = st.columns(2)
        ok = col1.button("OK", type="primary", use_container_width=True,
                         on_click=submit)
        cancel = col2.button("Cancel", type="secondary", use_container_width=True)
