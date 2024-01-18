import logging
import streamlit as st
from lib.sql_cmds import *
from lib.formatters import *

logging.basicConfig(level=logging.WARNING)

st.set_page_config(page_title="My Requests", page_icon="🤘",
                   layout="wide")

st.title("🤘 My Requests")
st.write("This page shows all requests that you have submitted.")


def make_manage_frame():
    data = st.session_state.my_requests
    with st.container(border=True):
        pending = [i for i in data[2] if i == "pending"]
        st.metric(label="Total/Pending", value=len(data), delta=len(pending))


def dataframe_with_selections(df):
    df_with_selections = df.copy()
    columns = ["request_id", "date_created", "approval_status",
               "date_approved", "xml_text"]
    df_with_selections.columns = columns
    df_with_selections.insert(0, "Select", False)

    # Get dataframe row-selections from user with st.data_editor
    edited_df = st.data_editor(
        df_with_selections,
        hide_index=True,
        column_config={
            "Select": st.column_config.CheckboxColumn(required=True)},
        disabled=df.columns,
        width=2000
    )

    # Filter the dataframe using the temporary column, then drop the column
    selected_rows = edited_df[edited_df.Select]
    # .drop('Select', axis=1)
    return selected_rows


def process_request(selected_row):
    # Make a copy of the selected row to avoid modifying the original DataFrame
    selected_row_copy = selected_row.copy()

    # Create a list of column-value pairs for the SET clause
    set_values = [
        f"xml_text = '{st.session_state.edit_request_text}'",
        f"approval_status = 'pending'",
        "date_approved = NULL"  # Set the datetime column to NULL
    ]

    # Join the SET clause using commas
    set_clause = ", ".join(set_values)

    # Create the WHERE clause
    where_clause = f"request_id = {selected_row_copy['request_id'].iloc[0]}"

    # Construct and execute the SQL query
    with connect(HOST, PORT, USER, PASSWORD) as conn:
        update(conn, "webapp_db", "requests", set_clause, where_clause)



def edit_request(selected_row):
    with st.expander("Edit Request", expanded=True):
        text = st.text_area("XML Text", value=selected_row["xml_text"].values[0],
                            height=300, key="edit_request_text")
        col1, col2 = st.columns(2)
        col1.button("Edit Request", type="primary", use_container_width=True, on_click=process_request,
                         args=[selected_row])

        if col2.button("Cancel", type="secondary", use_container_width=True):
            st.sidebar.warning("Request not edited.")
            st.rerun()


if "my_requests" not in st.session_state:
    st.session_state.my_requests = []
if "edit_request" not in st.session_state:
    st.session_state.edit_request = ""

if "user" in st.session_state and st.session_state.user != "":
    st.write(f"Requests for user: {st.session_state.user}")
    data = get_requests_by_user(st.session_state.user)
    data = pd.DataFrame(data)
    if len(data) > 0:
        st.session_state.my_requests = data
        my_req = dataframe_with_selections(data)
        make_manage_frame()
        selected_rows = my_req[my_req.Select]
        if st.button("Delete Selected Requests", type="primary",
                     disabled=True if len(selected_rows) == 0 else False):
            for i in [*selected_rows["request_id"]]:
                remove_user_request_by_id(i)
            st.sidebar.success("Rows removed")
            st.rerun()
        if st.button("Edit Selected Request", type="primary",
                     disabled=False if len(selected_rows) == 1 else True,
                     help="You can only edit one request at a time."):
            edit_request(selected_rows)
    else:
        st.write("You have no submitted requests.")
else:
    st.switch_page("New Request.py")
