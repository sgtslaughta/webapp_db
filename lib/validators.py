import re
import ipaddress


def expand_and_validate_ipv6(ipv6_address):
    try:
        # Try to expand and validate the IPv6 address
        expanded_address = ipaddress.IPv6Address(ipv6_address).exploded
        return expanded_address
    except ipaddress.AddressValueError as e:
        # Handle validation errors
        return f"Invalid IPv6 address: {e}"


def validate_email(email):
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return False
    return True


def validate_ipv4(ip):
    if not re.match(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", ip):
        return False
    return True


def validate_ssh_key(key):
    # Regular expression patterns for public and private SSH keys
    public_key_pattern = re.compile(r'^ssh-rsa\s[^\s]+\s[^\s]+')
    private_key_pattern = re.compile(r'^-----BEGIN\s(?:RSA|OPENSSH)\sPRIVATE\sKEY-----')

    # Check if it matches either public or private key pattern
    is_public_key = bool(public_key_pattern.match(key))
    is_private_key = bool(private_key_pattern.match(key))
    if not is_public_key and not is_private_key:
        return False
    return True
