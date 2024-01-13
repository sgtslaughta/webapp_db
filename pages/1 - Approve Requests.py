import streamlit as st
from lib.formatters import *
import logging

logging.basicConfig(level=logging.WARNING)


def fetch_data():
    with connect(HOST, PORT, USER, PASSWORD) as conn:
        if conn:
            return table_data_to_df(conn, "webapp_db", "requests")


def merge_dataframes(df1, df2):
    # Merge DataFrames on common 'id' columns
    merged_df = pd.merge(df1, df2, how='left', left_on='id_created_by',
                         right_on='user_id')
    merged_df = pd.merge(merged_df, df2, how='left', left_on='id_approved_by',
                         right_on='user_id',
                         suffixes=('_created_by', '_approved_by'))

    # Drop redundant columns
    merged_df = merged_df.drop(
        ['id_approved_by', 'user_id_created_by',
         'user_id_approved_by', 'date_user_created_created_by',
         'date_last_active_created_by', 'date_user_created_approved_by',
         'date_last_active_approved_by'],
        axis=1)

    # Rename columns
    merged_df = merged_df.rename(
        columns={'user_name_created_by': 'created_by',
                 'user_name_approved_by': 'approved_by'})
    column_order = ['request_id', 'date_created', 'created_by',
                    'id_created_by',
                    'approval_status', 'date_approved', 'approved_by',
                    'xml_text']
    merged_df = merged_df.reindex(columns=column_order)
    # Sort by status; pending
    merged_df = merged_df.sort_values(by=['approval_status'], ascending=False)

    return merged_df


def set_data():
    st.session_state.fetched_data = fetch_data()
    with connect(HOST, PORT, USER, PASSWORD) as conn:
        if conn:
            users_df = table_data_to_df(conn, "webapp_db", "users")
    new_df = merge_dataframes(st.session_state.fetched_data, users_df)
    st.session_state.fetched_data = new_df
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
    if "user" in st.session_state:
        st.sidebar.success("Rows submitted for approval")
        st.balloons()
        send_approvals_to_server(st.session_state.submissions,
                                 st.session_state.user)
        update_users_last_active(st.session_state.user)
    else:
        st.sidebar.warning("No user logged in")
    set_data()


st.title("All Requests")
st.write("This page shows all requests that have been submitted for "
         "approval. NOTE: Only requests made by others will  be displayed.")
if "user" in st.session_state and st.session_state.user != "":
    st.info(f"Logged in as: {st.session_state.user}")
    # get the user's ID from the database
    with connect(HOST, PORT, USER, PASSWORD) as conn:
        uid = get_user_id_from_name(conn, "webapp_db", "users",
                                    st.session_state.user)
        try:
            if uid['user_id']:
                uid = uid['user_id']
        except TypeError:
            pass
    # filter the df to remove requests created by the user
    if "fetch_data" not in st.session_state:
        set_data()
    if len(st.session_state.fetched_data) > 0:
        st.session_state.fetched_data = st.session_state.fetched_data[
            st.session_state.fetched_data['id_created_by'] != uid]
else:
    st.switch_page("New Request.py")

if "fetched_data" not in st.session_state:
    set_data()

if len(st.session_state.fetched_data) > 0:
    data = st.session_state.fetched_data
    total = data['approval_status'].value_counts()
    pending = total.get('pending', 0)
    st.metric(label="Total/Pending", value=len(data), delta=int(pending))
col1, col2, col3, col4, col5 = st.columns(5, gap="small")
with col5:
    st.button("🔄", on_click=set_data, help="Refresh data")
if len(st.session_state.fetched_data) > 0:
    selection = dataframe_with_selections(st.session_state.fetched_data)
else:
    st.write("No requests to display")
    st.stop()
st.write("<i>INFO: To view the request XML, scroll to the right inside the "
         "data"
         " table. Then double click the cell containing the XML text.<i>",
         unsafe_allow_html=True)
approve_txt = "Select as many items as you wish to approve, then click this " \
              "button."
approve = st.button("✔️ Approve & Submit", on_click=print_selected_rows,
                    args=[selection], type="primary", help=approve_txt)
if approve and len(selection) > 0:
    with st.container(border=True):
        st.info(
            "NOTE: If selection includes 'approved' requests, they will be "
            "re-submitted for transmittal.")
        st.write("Selected rows:")
        st.write(st.session_state.submissions)
        # st.session_state.submissions = []
        col1, col2 = st.columns(2)
        ok = col1.button("OK", type="primary", use_container_width=True,
                         on_click=submit)
        if ok:
            selection.loc[:, 'Select'] = False
            selected_rows = selection[selection.Select]
            selected_rows.drop('Select', axis=1)
        cancel = col2.button("Cancel", type="secondary",
                             use_container_width=True)
elif approve and len(selection) == 0:
    st.sidebar.warning("No rows selected for approval", icon="⚠️")

