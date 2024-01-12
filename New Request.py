import streamlit as st
from lib.validators import *
import logging

logging.basicConfig(level=logging.WARNING)


st.title("New Request")

st.markdown("""
Add as many items as you want to your request, then submit for approval.
Your request will be reviewed by the approver and you will be notified of the
status of your request via email.

""")

if "full_request" not in st.session_state:
    st.session_state.full_request = {}
    if "ssh_key" not in st.session_state.full_request:
        st.session_state.full_request["ssh_key"] = []
    if "email" not in st.session_state.full_request:
        st.session_state.full_request["email"] = []

def add_to_request(key, value):
    if value not in st.session_state.full_request[key]:
        st.session_state.full_request[key].append(value)

def remove_from_request(key):
    if key in st.session_state.full_request:
        del st.session_state.full_request[key]

def add_ssh_key(key):
    if validate_ssh_public_key(key) or validate_ssh_private_key(key):
        add_to_request("ssh_key", key)
    else:
        st.error("Invalid SSH Key")

def add_email(email, *args):
    if validate_email(email):
        add_to_request("email", email)
    else:
        st.error("Invalid email address")

def submit():
    print(st.session_state.full_request)

with st.container(border=True):
    ssh_key = st.text_input(label="SSH KEY", key="ssh_key", placeholder="SSH "
                                                                      "Key")
    add_ssh_button = st.button(label="Add SSH Key", on_click=add_ssh_key,
                               args=[ssh_key])
    email_address = st.text_input(label="Email Address", key="email_addr",
                                    placeholder="Email Address")
    add_email_button = st.button(label="Add Email", on_click=add_email,
                                 args=[email_address])
    st.text_area(label="Complete Request", value=st.session_state.full_request,
                 height=200)
    st.button(label="Submit Request for Approval",
              on_click=submit)

print(st.session_state.full_request)