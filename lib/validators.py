import re

def validate_email(email):
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return False
    return True

def validate_ipv4(ip):
    if not re.match(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", ip):
        return False
    return True

def expand_ipv6(ip):
    if "::" in ip:
        ip = ip.replace("::", ":" + "0:" * (8 - ip.count(":")))
    return ip

def validate_full_ipv6(ip):
    if not re.match(r"([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}", expand_ipv6(ip)):
        return False
    return True

def validate_ssh_private_key(key):
    if not re.match(r"^(ssh-(?:rsa|dss|ed25519|ecdsa) [A-Za-z0-9+/]+[=]{0,3}(?: [^@]+@[^@]+)?)$", key):
        return False
    return True

def validate_ssh_public_key(key):
    if not re.match(r"^(ssh-(?:rsa|dss|ed25519|ecdsa) [A-Za-z0-9+/]+[=]{0,3}(?: [^@]+@[^@]+)?)$", key):
        return False
    return True