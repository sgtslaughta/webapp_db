import logging
import streamlit as st
from lib.formatters import *
from time import sleep


logging.basicConfig(level=logging.WARNING)

st.title("My Requests")
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
    )

    # Filter the dataframe using the temporary column, then drop the column
    selected_rows = edited_df[edited_df.Select]
    # .drop('Select', axis=1)
    return selected_rows


if "my_requests" not in st.session_state:
    st.session_state.my_requests = []

if "user" in st.session_state and st.session_state.user != "":
    data = get_requests_by_user(st.session_state.user)
    data = pd.DataFrame(data)
    if len(data) > 0:
        st.session_state.my_requests = data
        my_req = dataframe_with_selections(data)
        make_manage_frame()
        if st.button("Remove Selected"):
            selected_rows = my_req[my_req.Select]
            for i in [*selected_rows["request_id"]]:
                remove_user_request_by_id(i)
            st.sidebar.success("Rows removed")
            st.rerun()
    else:
        st.write("You have no submitted requests.")
else:
    st.switch_page("New Request.py")

