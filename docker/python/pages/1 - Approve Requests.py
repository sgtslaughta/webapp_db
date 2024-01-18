import streamlit as st
import logging
import pandas as pd
import plotly.express as px
from lib.sql_cmds import *
from lib.formatters import *

logging.basicConfig(level=logging.WARNING)
st.set_page_config(page_title="Approve Requests", page_icon="🤝",
                   layout="wide")


def fetch_data():
    with connect(HOST, PORT, USER, PASSWORD) as conn:
        if conn:
            return table_data_to_df(conn, "webapp_db", "requests")


def merge_dataframes(df1, df2):
    # Print unique values and data types

    df1['id_approved_by'] = pd.to_numeric(df1['id_approved_by'], errors='coerce', downcast='signed')

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
        width=2000
    )

    # Filter the dataframe using the temporary column, then drop the column
    selected_rows = edited_df[edited_df.Select]
    return selected_rows.drop('Select', axis=1)


def print_selected_rows(rows):
    if "submissions" not in st.session_state:
        st.session_state.submissions = []
    st.session_state.submissions = rows


def get_and_merge_dataframes():
    req_df = fetch_data()
    with connect(HOST, PORT, USER, PASSWORD) as conn:
        if conn:
            users_df = table_data_to_df(conn, "webapp_db", "users")
    new_df = merge_dataframes(req_df, users_df)
    return new_df


def make_graphs(container):
    with container.expander(expanded=False, label="Graphs"):
        tab1, tab2, tab3 = st.tabs(["Approvals & Submissions", "Pending",
                                    "Timeline"])
        approvals_tab, submissions_tab = tab1.tabs(["Approvals",
                                                    "Submissions"])
        # Create a scatter plot of approvals by user
        dataframe = get_and_merge_dataframes()
        df = dataframe.copy()
        df['date_created'] = pd.to_datetime(df['date_created'])
        df['date_approved'] = pd.to_datetime(df['date_approved'])

        # Create a new DataFrame with only the relevant columns
        approval_data = df[['approved_by', 'date_approved']]

        # Group by 'approved_by' and count the number of approvals
        approval_counts = approval_data.groupby(
            ['approved_by', 'date_approved']).size().reset_index(
            name='approval_count')

        # Filter out non-positive values
        approval_counts = approval_counts[
            approval_counts['approval_count'] > 0]
        fig = px.scatter(approval_counts, x='approved_by', y='approval_count',
                         size='approval_count', color='approval_count',
                         hover_name='approved_by',
                         title="Approvals by User")

        approvals_tab.plotly_chart(fig, use_container_width=True)

        # Crate a scatter plot of submissions by user
        df_copy = dataframe.copy()

        # Convert 'date_created' and 'date_approved' columns to datetime objects
        df_copy['date_created'] = pd.to_datetime(df_copy['date_created'])
        df_copy['date_approved'] = pd.to_datetime(df_copy['date_approved'])

        # Create a new DataFrame with only the relevant columns
        submission_data = df_copy[['created_by', 'date_created']]

        # Group by 'approved_by' and count the number of submissions
        submission_counts = submission_data.groupby(
            'created_by').size().reset_index(name='submission_count')

        # Filter out non-positive values
        submission_counts = submission_counts[
            submission_counts['submission_count'] > 0]

        # Create a scatter plot using Plotly Express
        fig = px.scatter(submission_counts, x='created_by',
                         y='submission_count',
                         size='submission_count', color='submission_count',
                         hover_name='created_by',
                         title='Users with the Most Submissions (Scatter Plot)',
                         labels={'submission_count': 'Submission Count'})
        submissions_tab.plotly_chart(fig, use_container_width=True)

        # Create a bar chart of long-lasting pending requests
        df_copy = dataframe.copy()
        # Convert 'date_created' and 'date_approved' columns to datetime objects
        df_copy['date_created'] = pd.to_datetime(df_copy['date_created'])
        df_copy['date_approved'] = pd.to_datetime(df_copy['date_approved'])

        # Calculate the time pending in hours for each request
        df_copy['time_pending'] = (pd.to_datetime('now') - df_copy[
            'date_created']).dt.total_seconds() / 3600

        # Filter out approved requests (consider only pending requests)
        pending_data = df_copy[df_copy['approval_status'] == 'pending']

        # Sort pending requests by the time pending
        sorted_pending_data = pending_data.sort_values(by='time_pending',
                                                       ascending=False)

        fig = px.bar(sorted_pending_data, x='time_pending', y='request_id',
                     # switched x and y
                     color='time_pending', orientation='h',
                     # set orientation to horizontal
                     title='Pending Requests Sorted by Longest Time Pending (in Hours)',
                     labels={'time_pending': 'Time Pending (Hours)'},
                     hover_data=['date_created', 'date_approved',
                                 'approval_status'])
        tab2.plotly_chart(fig, use_container_width=True)

        df = dataframe.copy()
        approved_data = df[df['approval_status'] == 'approved']
        fig = px.timeline(approved_data,
                          x_start="date_created",
                          x_end="date_approved", y="created_by",
                          color="created_by", title="Timeline of "
                                                    "Approved Requests",
                          labels={'created_by': 'User',
                                  'date_created': 'Date Created',
                                  'date_approved': 'Date Approved'})
        tab3.plotly_chart(fig, use_container_width=True)
        tab3.write(
            "<i>NOTE: The timeline above shows the date the request was "
            "created and the date it was approved. The timeline does "
            "not show pending requests. This helps us see how long an"
            "average request takes to be approved.<i>",
            unsafe_allow_html=True)


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


st.title("🤝 Approve Requests")
st.markdown(
    "This page shows all requests that have been submitted for approval. "
    "NOTE: Only requests made by others will be displayed. "
    "To view your own requests click <a href='/My_Requests' target='_self'>here</a>.",
    unsafe_allow_html=True
)
if "user" in st.session_state and st.session_state.user != "":

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
    st.metric(label="Pending/Total", value=int(pending), delta=len(data))
if len(st.session_state.fetched_data) > 0:
    with st.container(border=True):
        st.write("Select rows to approve:")
        selection = dataframe_with_selections(st.session_state.fetched_data)
        st.button("🔄", on_click=set_data, help="Refresh data")
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
graph_container = st.container(border=True)
graph_container.subheader("Data Graphs", divider="rainbow")
graph_container.button("🔄 Make graphs", on_click=make_graphs, help="Generate "
                                                                   "the "
                                                                   "graphs",
                       args=[graph_container])
