import os

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


from openpype.lib import OpenPypeSecureRegistry

API_KEY_KEY = "api_key"


def get_aquarium_hostname(server_url=None):
    if not server_url:
        server_url = os.environ.get("AQUARIUM_SERVER_URL")

    if not server_url:
        return None

    if "//" not in server_url:
        server_url = "//" + server_url

    return urlparse(server_url).hostname


def _get_aquarium_secure_key(hostname, key):
    """Secure item key for entered hostname."""
    return "/".join(("aquarium", hostname, key))


def get_credentials(server_url=None):
    output = {
        API_KEY_KEY: None
    }
    hostname = get_aquarium_hostname(server_url)
    if not hostname:
        return output

    api_key_name = _get_aquarium_secure_key(hostname, API_KEY_KEY)
    api_key_registry = OpenPypeSecureRegistry(api_key_name)
    output[API_KEY_KEY] = api_key_registry.get_item(API_KEY_KEY, None)

    return output


def save_credentials(api_key, server_url=None):
    hostname = get_aquarium_hostname(server_url)
    api_key_name = _get_aquarium_secure_key(hostname, API_KEY_KEY)

    # Clear credentials
    clear_credentials(server_url)
    api_key_registry = OpenPypeSecureRegistry(api_key_name)
    api_key_registry.set_item(API_KEY_KEY, api_key)


def clear_credentials(ftrack_server=None):
    hostname = get_aquarium_hostname(ftrack_server)
    api_key_name = _get_aquarium_secure_key(hostname, API_KEY_KEY)
    api_key_registry = OpenPypeSecureRegistry(api_key_name)

    current_api_key = api_key_registry.get_item(API_KEY_KEY, None)
    if current_api_key is not None:
        api_key_registry.delete_item(API_KEY_KEY)


def check_credentials(api_key, server_url=None):
    if not server_url:
        server_url = os.environ.get("AQUARIUM_SERVER_URL")

    if not server_url or not api_key:
        return False

    user_exists = False
    try:
        # TODO implement validation of credentials
        pass

    except Exception:
        pass
    return user_exists
