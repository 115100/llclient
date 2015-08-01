"""Set of functions for load.link (https://github.com/deuiore/load.link) API.
"""
from getpass import getpass
import json
from os import remove
from os.path import basename, expanduser, isfile
from requests_toolbelt import MultipartEncoder
import re
import requests
import sys
import yaml


class Request:
    """Utility for quick requests to load.link
    """

    def __init__(self, config_file=None):
        self._config_reader(config_file)

    def _config_reader(self, config_file):
        """Attempt to open config file and read values
        needed to access load.link.
        """
        config_file = config_file or expanduser("~/.ll_config")
        try:
            fp = open(config_file, "r+")
        except (OSError, IOError):
            print("No config file found at: " + config_file)
            sys.exit(1)

        self._config = yaml.load(fp)
        try:
            self._root_url = self._config["URL"]
        except (IndexError, TypeError):
            print("No URL setting found in " + config_file)

            i = input("Do you want to set this now? [Y]")

            if i not in ('', 'Y'):
                sys.exit(1)

            self._config = {}
            self._config["URL"] = input("What is your /api URL? ")

            fp.seek(0)
            fp.truncate()
            fp.write(yaml.dump(self._config, default_flow_style=False))

            self._root_url = self._config["URL"]

        fp.close()

        if not re.match("^https?://.*/|\?api$", self._root_url):
            print("Invalid URL passed")
            sys.exit(1)

    def post_data(self, action, json_dict=None, data_tuple=None):
        """Generic function handling all POSTs to /api endpoint.
        """
        payload = {"action": action}

        if json_dict:
            payload.update(json_dict)

        if "username" not in payload:
            payload["token"] = self._get_token()

        payload = {
            "headers": (
                "headers",
                bytes(
                    json.dumps(payload),
                    "utf-8"),
                "application/json")}

        if data_tuple:
            payload["data"] = data_tuple

        me = MultipartEncoder(payload)

        response = requests.post(
            self._root_url,
            data=me,
            headers={
                "content-type": me.content_type})

        try:
            response.raise_for_status()
        except:
            raise Exception(
                "Error {error_code} with {action}: {error}".format(
                    error_code=response.status_code,
                    action=action,
                    error=response.text))

        return response

    def _get_token(self, token_path=expanduser("~/.ll_token")):
        """Check token_path for token if it exists
        or retrieve token from user input.
        """
        if isfile(token_path):
            with open(token_path, 'r') as f:
                token = f.readline()
                if token:
                    return token

        username = input("What is your username? ")
        password = getpass("What is your password? ")

        response = self.post_data(
            "get_token", {
                "username": username, "password": password})

        token = response.json()["token"]

        with open(token_path, 'w') as f:
            f.write(token)

        return token

SERVICE = Request()


def get_links(limit, offset):
    """Get `limit` links starting from `offset`."""
    response = SERVICE.post_data(
        "get_links", {"limit": limit, "offset": offset})

    return response.json()["links"]


def count():
    """Return count of all uploaded items."""
    response = SERVICE.post_data("count")

    return response.json()["count"]


def get_thumbnail(uid):
    """Return thumbnail and associated details for `uid`.
    """
    response = SERVICE.post_data("get_thumbnail", {"uid": uid})

    return response.json()["thumbnail"]


def upload(file_path):
    """Upload file `file_path`."""
    with open(file_path, 'rb') as fp:

        file_name = basename(file_path)

        response = SERVICE.post_data("upload", {"filename": file_name}, ("data", fp, ''))

    if response.status_code == 202:
        print("Failed to upload " + file_path)
        return
    # Might change to return whole dictionary
    return response.json()["link"]


def shorten_url(url):
    """Shorten `url`."""
    response = SERVICE.post_data("upload", {"url": url})

    return response.json()["link"]


def delete(uid):
    """Delete uploaded item `uid`."""
    response = SERVICE.post_data("delete", {"uid": uid})

    if response.status_code != 200:
        print("Failed to remove uid: " + uid)


def edit_settings(settings_dict):
    """Edit load.link settings.
    """
    password = getpass("What is your password? ")

    response = SERVICE.post_data(
        "edit_settings", {
            "password": password, "settings": json.dumps(settings_dict)})

    if response.status_code != 200:
        print("Failed to update settings: " + response.json()["message"])


def release_token(token_path=expanduser("~/.ll_token")):
    """Release token at `token_path` and remove it.
    """
    if not token_path or not isfile(token_path):
        print(token_path + " doesn't exist to release")
        return
    response = SERVICE.post_data("release_token")

    if response.status_code == 200:
        remove(token_path)
        return

    print("Failed to release token")


def release_all_tokens(token_path=expanduser("~/.ll_token")):
    """Release all authentication tokens and delete `token_path`.
    """
    if not token_path or not isfile(token_path):
        print(token_path + " doesn't exist to release")
        return
    response = SERVICE.post_data("release_all_tokens")

    if response.status_code == 200:
        remove(token_path)
        return

    print("Failed to release all tokens")


def prune_unused():
    """Prune unused links."""
    response = SERVICE.post_data("prune_unused")

    return response.json()["pruned"]
