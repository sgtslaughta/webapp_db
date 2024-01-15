import streamlit as st
from lib.validators import *
from lib.formatters import *
import logging
from io import StringIO
from re import split
import datetime
import yaml
from streamlit.web.server.websocket_headers import _get_websocket_headers

headers = _get_websocket_headers()
#access_token = headers.get("X-Access-Token")
if headers is not None:
    st.session_state['headers'] = headers

DELIM = r'\r?\n'  # Regex to split on comma or whitespace
PRIV_KEY_REGEX = r'-{3,}BEGIN.*-{3,}\n[\s\S]*?\n-{3,}.*KEY-{3,}'
PUB_KEY_REGEX = r'ssh-.*\b'

logging.basicConfig(level=logging.WARNING)


def load_parse_csv(csv):
    """Load and parse CSV file"""
    stringio = StringIO(csv.getvalue().decode("utf-8"))
    df = pd.read_csv(stringio)
    return df


def set_user():
    if "user" not in st.session_state:
        st.session_state["user"] = ""
    if st.session_state.user == "":
        user = st.sidebar.text_input(label="Username:",
                                     key="active-user").lower()
        if user != "":
            st.session_state.user = user
            # add user to DB
            add_user_to_db(user)
            st.sidebar.success(f"👋 Welcome, {st.session_state.user}!")
    return st.session_state.user


def add_to_request(value, val_type=None, val_subtype=None):
    cur_grp = st.session_state["current_group"]
    main_key = st.session_state.group_draft[cur_grp][val_type]
    if val_type == "ssh_keys":
        if value in main_key[val_subtype]:
            val = value[:50] + "..."
            st.sidebar.error(f"Item already in request: {val}",
                             icon="⚠️")
            return False
        else:
            main_key[val_subtype].append(value)
    elif value not in main_key:
        main_key.append(value)
    else:
        # trunk the value down to the first 10 chars
        value = value[:50] + "..."
        st.sidebar.error(f"Item already in request: {value}", icon="⚠️")
        return False
    return True


def remove_from_request(value):
    if value in st.session_state.group_draft:
        st.session_state.group_draft.remove(value)


def add_username(value):
    if not value:
        st.sidebar.error("Username cannot be empty", icon="⚠️")
        return
    username_list = split(DELIM, value.rstrip())
    cnt = 0
    for user in username_list:
        if add_to_request(item_to_xml("username", user), "usernames"):
            cnt += 1
    if cnt:
        st.sidebar.success(f"{cnt} Usernames added!")
    update_draft()


def add_ssh_key(value):
    if not value:
        st.sidebar.error("SSH Key cannot be empty", icon="⚠️")
        return
    ssh_private_keys = re.finditer(PRIV_KEY_REGEX, value)
    ssh_public_keys = re.finditer(PUB_KEY_REGEX, value)
    cnt = 0
    for key in ssh_private_keys:
        if add_to_request(item_to_xml("ssh_key", key.group()), "ssh_keys",
                          "private"):
            cnt += 1
    for key in ssh_public_keys:
        if add_to_request(item_to_xml("ssh_key", key.group()), "ssh_keys",
                          "public"):
            cnt += 1
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
            if add_to_request(item_to_xml("ipv4", i), "ip_addresses"):
                cnt += 1
                continue
            else:
                continue
        ipv6 = expand_and_validate_ipv6(i)
        if 'Invalid' not in ipv6:
            if add_to_request(item_to_xml("ipv6", ipv6), "ip_addresses"):
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
        if add_to_request(item_to_xml("email", e), "email_addresses"):
            cnt += 1
    if cnt > 0:
        st.sidebar.success(f"{cnt} Email Addresses added!")
    update_draft()


def dict_to_xml(dictionary, indent=0):
    xml_string = ""
    tab = '\t'
    for key, value in dictionary.items():
        if isinstance(value, dict):
            xml_string += dict_to_xml(value, indent + 2)
        elif isinstance(value, list):
            for item in value:
                xml_string += f"{tab * indent}{item}\n"
        else:
            xml_string += f"{tab * indent}{value}\n"
    return xml_string


def update_draft():
    request = st.session_state.group_draft[st.session_state.current_group]
    rqst_str = f"<{st.session_state.current_group}>\n"
    xml = dict_to_xml(request, 1)
    rqst_str += xml
    rqst_str += f"</{st.session_state.current_group}>"
    st.session_state.group_str = rqst_str


def submit_request():
    user = st.session_state.user
    if not user:
        st.sidebar.error("Username cannot be empty", icon="⚠️")
        return
    if not st.session_state.group_draft:
        st.sidebar.error("Request cannot be empty", icon="⚠️")
        return

    with connect(HOST, PORT, USER, PASSWORD) as conn:
        if conn:
            uid = get_user_id_from_name(conn, "webapp_db", "users", user)
            # Check if user exists in DB
            if not uid:
                # Add user to DB
                add_entry_to_table(conn, "webapp_db", "users",
                                   {"user_name": user})
            try:
                if uid['user_id']:
                    uid = uid['user_id']
            except TypeError:
                pass
            # Add request to DB
            update_draft()
            draf_text = "".join(st.session_state.full_request_draft)
            xml_text = draf_text
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
            st.balloons()
            st.session_state.group_draft = {}
            st.session_state.group_str = ""
            st.session_state.full_request_draft = []
            st.session_state.current_group = "group_1"


def file_handler(yml_data):
    string_data = yml_data.read().decode("utf-8")
    cnt = 0
    try:
        yml_dict = yaml.load(string_data, Loader=yaml.FullLoader)
    except yaml.YAMLError as e:
        st.sidebar.error(f"Error parsing YML: {e}", icon="⚠️")
        return
    try:
        for group in yml_dict:
            for item in group:
                for i in group[item]:
                    if i == "ssh_keys":
                        for key, value in group[item][i].items():
                            for j in value:
                                if add_to_request(item_to_xml("ssh_key", j),
                                                  "ssh_keys", key):
                                    cnt += 1
                    elif i == "email_addrs":
                        for email in group[item][i]:
                            if add_to_request(item_to_xml("email", email),
                                              "email_addresses"):
                                cnt += 1
                    elif i == "ip_addrs":
                        for ip in group[item][i]:
                            if add_to_request(item_to_xml("ip", ip),
                                              "ip_addresses"):
                                cnt += 1
                    elif i == "user_names":
                        for user in group[item][i]:
                            if add_to_request(item_to_xml("username", user),
                                              "usernames"):
                                cnt += 1
            update_draft()
            add_group_to_request()
    except Exception as e:
        st.sidebar.error(f"Error parsing YML: {e}", icon="⚠️")
        return
    if cnt > 0:
        st.sidebar.success(f"{cnt} items added from file")


def clear_group():
    st.session_state.group_str = ""
    st.session_state.group_draft[st.session_state.current_group] = make_dict()
    make_dict()
    update_draft()


def add_group_to_request():
    group_cnt = len(st.session_state.group_draft) + 1
    grp_name = f"group_{group_cnt}"
    st.session_state["current_group"] = grp_name
    st.session_state.group_draft[grp_name] = make_dict()
    text = st.session_state.group_str
    st.session_state.full_request_draft.append(f"{text}\n")
    st.session_state.group_str = ""


def make_dict():
    group_dict = {'ssh_keys': {'public': [], 'private': []},
                  'email_addresses': [],
                  'ip_addresses': [],
                  'usernames': []}
    return group_dict


def count_items(dictionary):
    count = 0
    for key, value in dictionary.items():
        for k, v in value.items():
            if isinstance(v, list):
                count += len(v)
            elif isinstance(v, dict):
                for i in v:
                    count += len(v[i])
    return count


def explode_dict(d, result=None, current_key=None):
    if result is None:
        result = []
    if isinstance(d, dict):
        for key, value in d.items():
            if current_key is not None:
                new_key = f"{current_key}.{key}"
            else:
                new_key = key
            explode_dict(value, result, new_key)
    elif isinstance(d, list):
        for i, item in enumerate(d):
            explode_dict(item, result, f"{current_key}[{i}]")
    else:
        result.append(d)
    return result


def remove_items_from_dict(values_to_remove, d):
    if isinstance(d, dict):
        for item in d:
            if isinstance(item, dict):
                remove_items_from_dict(values_to_remove, item)
    elif isinstance(d, list):
        for i, item in enumerate(d):
            if item in values_to_remove:
                d.remove(item)
            else:
                remove_items_from_dict(values_to_remove, item)


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

    if "group_draft" not in st.session_state:
        st.session_state.group_draft = {}
    if "group_str" not in st.session_state:
        st.session_state.group_str = ""
    if "group_1" not in st.session_state.group_draft:
        st.session_state.group_draft["group_1"] = make_dict()
    if "current_group" not in st.session_state:
        st.session_state.current_group = "group_1"
    if "full_request_draft" not in st.session_state:
        st.session_state.full_request_draft = []


def draw_adders():
    st.subheader("🌟 Create a new group", divider="rainbow")
    with ((st.container(border=True))):
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

        if st.session_state.group_str != "":
            val = st.session_state.group_str
        else:
            val = "Your group is empty..."
        # st.metric(label="Total Items In Draft:", value=count_items(
        #     st.session_state.full_request))
        draft = st.text_area(label="Group (Draft)", value=val,
                             height=200,
                             help="This is a draft of your group. Drag"
                                  " the bottom right corner to expand.")
        col1, col2 = st.columns(2)
        if st.session_state.group_str != "":
            is_empty = False
        else:
            is_empty = True
        pressed = col1.button(label="Add group to request",
                              on_click=add_group_to_request,
                              use_container_width=True, type="primary",
                              disabled=is_empty)
        if pressed:
            draft = ''
        col2.button(label="Clear group", on_click=clear_group,
                    use_container_width=True, type="secondary")
        st.write("If you would like to remove values from your group, "
                 "click the button below 👇")
        with st.expander(label="Remove values from group", expanded=False):
            try:
                items = explode_dict(st.session_state.group_draft[
                                         st.session_state.current_group])
                with st.form(key="remove_values_form",
                             clear_on_submit=True):
                    options = st.multiselect(
                        label="Select values to remove",
                        options=items,
                        key="remove_values")
                    TODO: "Fix this so that vals are removed from the dict"
                    gdict = st.session_state.group_draft
                    groupd = gdict[st.session_state.current_group]
                    if st.form_submit_button(
                            label="Remove selected values",
                            type="primary",
                            on_click=remove_items_from_dict,
                            args=[options, groupd]):
                        st.sidebar.success("Values removed")
                        update_draft()
                        draft = st.session_state.group_str
            except IndexError:
                pass


def draw_file_upload():
    st.subheader("📤 Bulk Upload", divider="rainbow")
    with st.expander(label="Bulk Upload", expanded=False):
        with st.container(border=True):
            st.write("OPTIONAL: Upload YML items in bulk.")
            with st.form(key="upload_yml", clear_on_submit=True):
                upload_file = st.file_uploader(label="Upload Template",
                                               type=["yml", "yaml"])
                submit_button = st.form_submit_button(label="Upload")
                if submit_button and upload_file is not None:
                    st.info("YML uploaded")
                    file_handler(upload_file)
                    update_draft()
                    st.rerun()
            with st.container(border=True):
                with open("template.yml", "r") as f:
                    st.download_button(label="📥 Download YML Template",
                                       data=f,
                                       file_name="template.yml",
                                       mime="text/yml")
                    st.write(
                        "<i>NOTE: This template provides an example of how "
                        "to "
                        "structure your YML file. Be mindful of the "
                        "format.</i>",
                        unsafe_allow_html=True)


def remove_groups_from_request(group_list):
    try:
        for group in group_list:
            st.session_state.full_request_draft.remove(group)
    except KeyError:
        pass


def draw_submit():
    st.subheader("✅ Submit Request", divider="rainbow")
    to_expand = True if len(st.session_state.full_request_draft) > 0 else \
        False
    with ((st.expander(label="Expand", expanded=to_expand))):
        st.write(
            "The preview below contains all groups that you have added to "
            "your request. If you would like to remove a group, click the "
            "button below 👇")
        with st.container(border=True):
            draf_len = len(st.session_state.full_request_draft)
            if draf_len > 0:
                draft_txt = "".join(st.session_state.full_request_draft)
            else:
                draft_txt = "Your request is empty..."
            full_request = st.text_area(label="Full Request (Draft)",
                                        height=500, value=draft_txt, )
            selected_groups = st.multiselect(label="Remove group from request",
                                             options=st.session_state.full_request_draft,
                                             key="remove_groups")
            show_rem_group_button = (False if len(selected_groups) >= 1 else
                                     True)
            rem_group_button = st.button(label="Remove selected groups",
                                         disabled=show_rem_group_button,
                                         on_click=remove_groups_from_request,
                                         args=[selected_groups],
                                         use_container_width=True, )
            col1, col2 = st.columns(2)
            show_submit = False if len(
                st.session_state.full_request_draft) > 0 else True
            submit_button = col1.button(label="Submit Request for Approval",
                                        on_click=submit_request,
                                        use_container_width=True,
                                        type="primary", disabled=show_submit,
                                        help="Submit your request for approval, "
                                             "button is disabled if request is "
                                             "empty.")
            clear_button = col2.button(label="Clear Request", type="secondary",
                                       use_container_width=True,
                                       on_click=clear_group)


setup_page()
draw_adders()
draw_file_upload()
draw_submit()
