"""Aquarium credentials functions."""

import os
from typing import Tuple, Optional
from .vendors.aquarium import Aquarium

from openpype.lib.local_settings import OpenPypeSecureRegistry
from openpype.lib import emit_event

def me(
    token: str, url: Optional[str] = None, domain: Optional[str] = None
):
    """Validate credentials by trying to connect to Aquarium host URL.

    Args:
        token (str): Aquarium user token
        url (str, optional): Aquarium host URL. Defaults to None.
        domain (str, optional): Aquarium domain. Defaults to None.

    Returns:
        Aquarium.User: Aquarium user object
    """

    if url is None:
        url = os.environ.get("AQUARIUM_SERVER_URL")

    if domain is None:
        domain = os.environ.get("AQUARIUM_DOMAIN")

    # Authenticate
    aq = Aquarium(api_url=url, domain=domain, token=token)
    return aq.me()


def validate_credentials(
    token: str, url: Optional[str] = None, domain: Optional[str] = None
) -> bool:
    """Validate credentials by trying to connect to Aquarium host URL.

    Args:
        token (str): Aquarium user token
        url (str, optional): Aquarium host URL. Defaults to None.
        domain (str, optional): Aquarium domain. Defaults to None.

    Returns:
        bool: Are credentials valid?
    """

    try:
        me(token, url, domain)
    except:
        return False

    return True

def signin(email: str, password: str, url: Optional[str] = None, domain: Optional[str] = None) -> str:
    """Sign in to Aquarium and get user token.

    Args:
        email (str): Aquarium user email.
        password (str): Aquarium user password.
        url (str, optional): Aquarium host URL. Defaults to None.
        domain (str, optional): Aquarium domain. Defaults to None.

    Returns:
        str: Aquarium user token
    """
    if url is None:
        url = os.environ.get("AQUARIUM_SERVER_URL")

    if domain is None:
        domain = os.environ.get("AQUARIUM_DOMAIN")

    # Authenticate
    aq = Aquarium(api_url=url, domain=domain)

    aq.signin(email, password)

    return aq.token

def validate_host(url: str, domain: Optional[str] = None) -> bool:
    """Validate credentials by trying to connect to Aquarium host URL.

    Args:
        url (str, optional): Aquarium host URL.
        domain (str, optional): Aquarium domain.

    Returns:
        bool: Is host valid?
    """
    # Connect to server

    aq = Aquarium(api_url=url, domain=domain)

    # Test host
    if aq.ping():
        return True
    else:
        raise Exception(
            "Enable to ping Aquarium server {0}".format(aquarium_url))


def clear_credentials():
    """Clear credentials in Secure Registry."""
    (token) = load_credentials()
    if token is None:
        return

    # Get user registry
    user_registry = OpenPypeSecureRegistry("aquarium_user")

    # Set local settings
    if token is not None:
        user_registry.delete_item("token")


def save_credentials(token: str):
    """Save credentials in Secure Registry.

    Args:
        token (str): Aquarium user token
    """
    # Get user registry
    user_registry = OpenPypeSecureRegistry("aquarium_user")

    # Set local settings
    user_registry.set_item("token", token)


def load_credentials() -> Tuple[str, str]:
    """Load registered credentials.

    Returns:
        Tuple[str, str]: (Token)
    """
    # Get user registry
    user_registry = OpenPypeSecureRegistry("aquarium_user")

    return user_registry.get_item("token", None)


def set_credentials_envs(token: str):
    """Set environment variables with Aquarium token.

    Args:
        token (str): Aquarium user token
    """
    os.environ["AQUARIUM_TOKEN"] = token
