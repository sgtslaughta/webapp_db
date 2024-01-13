import pandas as pd
import streamlit as st
from lib.validators import *
from lib.formatters import *
import logging
from io import StringIO
from re import split
from time import sleep
import datetime
import csv
from streamlit.web.server.websocket_headers import _get_websocket_headers

headers = _get_websocket_headers()
access_token = headers.get("X-Access-Token")
if headers is not None:
    print(headers)

DELIM = r'\r?\n'  # Regex to split on comma or whitespace

logging.basicConfig(level=logging.WARNING)


def load_parse_csv(csv):
    """Load and parse CSV file"""
    stringio = StringIO(csv.getvalue().decode("utf-8"))
    df = pd.read_csv(stringio)
    return df


def set_user():
    if "user" not in st.session_state:
        st.session_state.user = ""
    if st.session_state.user == "":
        user = st.sidebar.text_input(label="Username:",
                                     key="active-user").lower()
        if user != "":
            st.session_state.user = user
            # add user to DB
            add_user_to_db(user)
            st.sidebar.success(f"👋 Welcome, {st.session_state.user}!")
    return st.session_state.user


def add_to_request(value):
    if value not in st.session_state.full_request:
        st.session_state.full_request.append(value)
    else:
        # trunk the value down to the first 10 chars
        value = value[:50] + "..."
        st.sidebar.error(f"Item already in request: {value}", icon="⚠️")


def remove_from_request(value):
    if value in st.session_state.full_request:
        st.session_state.full_request.remove(value)


def add_username(value):
    if not value:
        st.sidebar.error("Username cannot be empty", icon="⚠️")
        return
    username_list = split(DELIM, value.rstrip())
    for user in username_list:
        add_to_request(item_to_xml("username", user))
    st.sidebar.success(f"{len(username_list)} Usernames added!")
    update_draft()


def add_ssh_key(value):
    if not value:
        st.sidebar.error("SSH Key cannot be empty", icon="⚠️")
        return
    ssh_list = split(',', value.rstrip())
    cnt = 0
    for key in ssh_list:
        if validate_ssh_key(key):
            cnt += 1
            add_to_request(item_to_xml("ssh_key", key))
        else:
            st.sidebar.error(f"Invalid SSH Key: {key}", icon="⚠️")
    if cnt > 0:
        st.sidebar.success(f"{cnt} SSH Keys added!")
    update_draft()


def add_ip_address(ip):
    if not ip:
        st.sidebar.error("IP address cannot be empty", icon="⚠️")
        return
    ip_list = split(DELIM, ip.rstrip())
    cnt = 0
    for i in ip_list:
        if validate_ipv4(i):
            add_to_request(item_to_xml("ipv4", i))
            cnt += 1
            continue
        ipv6 = expand_and_validate_ipv6(i)
        if ipv6:
            add_to_request(item_to_xml("ipv6", ipv6))
            cnt += 1
        else:
            st.sidebar.error(f"Invalid IP address: {i}", icon="⚠️")
    if cnt > 0:
        st.sidebar.success(f"{cnt} IP Addresses added!")
    update_draft()


def add_email(email):
    if not email:
        st.sidebar.error("Email address cannot be empty", icon="⚠️")
        return
    email_list = split(DELIM, email.rstrip())
    cnt = 0
    for e in email_list:
        if not validate_email(e):
            st.sidebar.error(f"Invalid email address: {e}", icon="⚠️")
            continue
        add_to_request(item_to_xml("email", e))
        cnt += 1
    if cnt > 0:
        st.sidebar.success(f"{cnt} Email Addresses added!")
    update_draft()


def update_draft():
    request = st.session_state.full_request
    rqst_str = ""
    for item in request:
        if isinstance(item, str):
            rqst_str += f"{item}\n"
        else:
            rqst_str += str(item) + "\n"
    st.session_state.full_request_str = rqst_str


def submit_request():
    user = st.session_state.user
    if not user:
        st.sidebar.error("Username cannot be empty", icon="⚠️")
        return
    if not st.session_state.full_request:
        st.sidebar.error("Request cannot be empty", icon="⚠️")
        return

    with connect(HOST, PORT, USER, PASSWORD) as conn:
        if conn:
            query = f"SELECT user_name FROM users WHERE user_name = '{user}'"
            result = execute_query(conn, query)
            # Check if user exists in DB
            if not result:
                # Add user to DB
                add_entry_to_table(conn, "webapp_db", "users",
                                   {"user_name": user})
            # get the users id
            uid = get_user_id_from_name(conn, "webapp_db", "users", user)
            try:
                if uid['user_id']:
                    uid = uid['user_id']
            except TypeError:
                pass
            # Add request to DB
            update_draft()
            xml_text = st.session_state.full_request_str
            current_datetime = datetime.datetime.now()
            formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
            vals = {"xml_text": xml_text,
                    "id_created_by": uid,
                    "date_created": formatted_datetime}
            add_entry_to_table(conn, "webapp_db", "requests", vals)
            # update users last active date
            if "user" in st.session_state:
                update_users_last_active(st.session_state.user)
            st.sidebar.success("Request submitted for approval")


def csv_handler(csv):
    string_data = csv.read().decode("utf-8")
    priv_keys, otherlines = capture_private_keys_and_other_lines(string_data)
    cnt = 0
    for line in otherlines:
        if line == "":
            continue
        if "email," in line:
            add_email(line.replace("email,", ""))
            cnt += 1
            continue
        if "ssh_key," in line:
            add_ssh_key(line.replace("ssh_key,", ""))
            cnt += 1
            continue
        if "username," in line:
            add_username(line.replace("username,", ""))
            cnt += 1
            continue
        if "ip," in line:
            add_ip_address(line.replace("ip,", ""))
            cnt += 1
            continue
    for key in priv_keys:
        add_ssh_key(key)
        cnt += 1
    if cnt > 0:
        st.sidebar.success(f"{cnt} items added from CSV")
    update_draft()


def clear_request():
    st.session_state.full_request_str = ""
    st.session_state.full_request = []
    update_draft()


def setup_page():
    st.set_page_config(page_title="New Request", page_icon="📝",
                       layout="wide",
                       menu_items={"About": "This is a tool to help you "
                                            "create a request. Simply fill "
                                            "in the "
                                            "fields and submit your "
                                            "request for approval. "
                                            "Once approved, the request"
                                            "be transmitted."}
                       )
    set_user()

    if not st.session_state.user:
        st.sidebar.error("Username cannot be empty", icon="⚠️")
        st.title("⚠️ Please enter a username to continue...")
        st.stop()

    st.title("📝 New Request")
    st.markdown("""
    Requests are broken down in to groups.
    Add as many items as you want to your group, then add your group to the 
    request. Continue adding groups as you desire. When ready submit the 
    completed requests for approval. Once approved, they will be 
    processed for transmittal.
    """)

    st.write("<i>NOTE: All fields accept multiple values of a given type, "
             "separated by new lines.</i>",
             unsafe_allow_html=True)

    if "full_request" not in st.session_state:
        st.session_state.full_request = []
    if "full_request_str" not in st.session_state:
        st.session_state.full_request_str = ""


def draw_adders():
    st.subheader("Create a new group", divider="rainbow")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1.expander(label="➕ SSH Key", expanded=False):
            st.write("Add public or private SSH keys to your request.")
            ssh_key = st.text_area(label="SSH KEY", key="ssh_key",
                                   placeholder="SSH "
                                               "Keys (Public or Private key, "
                                               "each on a new line. "
                                               "Copy entire key including '"
                                               "-----BEGIN OPENSSH PRIVATE "
                                               "KEY-----' to end)...",
                                   height=200)
            add_ssh_button = st.button(label="Add SSH Key",
                                       on_click=add_ssh_key,
                                       args=[ssh_key])
        with col2.expander(label="➕ Email Address", expanded=False):
            email_address = st.text_area(label="Email Address",
                                         key="email_addr",
                                         placeholder="Email Addresses (new line "
                                                     "separated)...",
                                         height=100)
            add_email_button = st.button(label="Add Emails (new line "
                                               "separated)",
                                         on_click=add_email,
                                         args=[email_address])
        col1, col2 = st.columns(2)
        with col1.expander(label="➕ IP Addresses", expanded=False):
            st.write("Add IPv4 or IPv6 addresses to your request.")
            ip_address = st.text_area(label="IP Address", key="ip_addr",
                                      placeholder="IP Addresses (IPv4 or IPv6, "
                                                  "new line separated)...",
                                      height=100)
            add_ip_button = st.button(label="Add IP Address",
                                      on_click=add_ip_address,
                                      args=[ip_address])
        with col2.expander(label="➕ Usernames", expanded=False):
            st.write("Add one or more usernames to your request, comma.")
            username = st.text_area(label="Username", key="username",
                                    placeholder="Usernames (new line "
                                                "separated)...",
                                    height=100)
            add_username_button = st.button(label="Add Username",
                                            on_click=add_username,
                                            args=[username])

        if st.session_state.full_request_str != "":
            val = st.session_state.full_request_str
        else:
            val = "Your group is empty..."
        st.metric(label="Total Items In Draft:", value=len(
            st.session_state.full_request))
        st.text_area(label="Group (Draft)", value=val,
                     height=200, help="This is a draft of your group. Drag"
                                      " the bottom right corner to expand.")
        col1, col2 = st.columns(2)
        col1.button(label="Add group to request", on_click=update_draft,
                    use_container_width=True, type="primary")
        col2.button(label="Clear group", on_click=clear_request,
                    use_container_width=True, type="secondary")
        st.write("If you would like to remove values from your group, "
                 "click the button below 👇")
        with st.expander(label="Remove values from group", expanded=False):
            try:
                options = st.multiselect(label="Select values to remove",
                                         options=st.session_state.full_request,
                                         key="remove_values")
                if options:
                    if st.button(label="Remove selected values",
                                 type="primary"):
                        cnt = 0
                        total = len(options)
                        txt = "Removing values..."
                        progress_bar = st.progress(0, text=txt)
                        for i in options:
                            remove_from_request(i)
                            cnt += 1
                            progress_percentage = cnt / total
                            progress_bar.progress(progress_percentage,
                                                  text=txt)
                            sleep(0.1)
                        progress_bar.empty()
                        st.sidebar.success("Values removed")
                        update_draft()
                        st.rerun()
            except IndexError:
                pass


def draw_file_upload():
    st.subheader("Bulk Upload", divider="rainbow")
    with st.expander(label="📤 Bulk Upload", expanded=False):
        with st.container(border=True):
            st.write("OPTIONAL: Upload CSV of SSH Keys and Email Addresses")
            upload_csv = st.file_uploader(label="Upload CSV", type="csv")
            if upload_csv:
                st.info("CSV uploaded")
                csv_handler(upload_csv)
            with st.container(border=True):
                with open("template.csv", "r") as f:
                    st.download_button(label="📥 Download CSV Template",
                                       data=f,
                                       file_name="template.csv",
                                       mime="text/csv")
                    st.write(
                        "<i>NOTE: This template provides an example of how "
                        "to "
                        "format your CSV file. You may delete the rows "
                        "containing example data, but do not delete the "
                        "header row.</i>", unsafe_allow_html=True)


def draw_submit():
    st.subheader("Submit Request", divider="rainbow")
    with st.container(border=True):
        full_request = st.text_area(label="Full Request", value="",
                                    height=400, key="full_request")
        selected_groups = st.multiselect(label="Select groups to remove",
                                         options=st.session_state.full_request,
                                         key="remove_groups")
        col1, col2 = st.columns(2)
        submit_button = col1.button(label="Submit Request for Approval",
                                    on_click=submit_request,
                                    use_container_width=True,
                                    type="primary", disabled=True if len(
                st.session_state.full_request) == 0 else False,
                                    help="Submit your request for approval, "
                                         "button is disabled if request is "
                                         "empty.")
        clear_button = col2.button(label="Clear Request", type="secondary",
                                   use_container_width=True,
                                   on_click=clear_request)


setup_page()
draw_adders()
draw_file_upload()
draw_submit()
