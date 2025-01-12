"""Set of functions for load.link (https://github.com/deuiore/load.link) API."""

from getpass import getpass
import json
import os
import re
from typing import (
    cast,
    BinaryIO,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)

from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
from clint.textui.progress import Bar as ProgressBar
import requests
import yaml


class Service:
    """Utility for quick requests to load.link"""

    def __init__(self, config_file: Optional[str] = None) -> None:
        self._config_reader(config_file)

    def _config_reader(self, config_file: Optional[str] = None) -> None:
        """Attempt to open config file and read values
        needed to access load.link.
        """
        config_file = config_file or os.path.expanduser("~/.config/llclient/config")
        try:
            cfg = open(config_file, "r+")
        except (OSError, IOError):
            os.makedirs(os.path.dirname(config_file))
            cfg = open(config_file, "w+")

        self._config = yaml.safe_load(cfg)
        try:
            self._root_url = self._config["URL"]
        except (IndexError, TypeError):
            print("No URL setting found in " + config_file)

            i = input("Do you want to set this now? [Y]")

            if i not in ("", "Y"):
                raise Exception("Unset configuration")

            self._config = {}
            self._config["URL"] = input("What is your /api URL? ")

            cfg.seek(0)
            cfg.truncate()
            cfg.write(yaml.dump(self._config, default_flow_style=False))

            self._root_url = self._config["URL"]

        cfg.close()

        if not re.match(r"^https?://.*/|\?api$", self._root_url):
            raise Exception("Invalid URL passed")

    def get_links(self, limit: str, offset: str) -> List[Dict[str, str]]:
        """Get `limit` links starting from `offset`."""
        response = cast(
            Dict[str, List[Dict[str, str]]],
            self._post_data("get_links", {"limit": limit, "offset": offset}).json(),
        )
        return response["links"]

    def count(self) -> int:
        """Return count of all uploaded items."""
        resp = cast(Dict[str, int], self._post_data("count").json())
        return resp["count"]

    def get_thumbnail(self, uid: str) -> Dict[str, str]:
        """Return thumbnail and associated details for `uid`."""
        response = cast(
            Dict[str, Dict[str, str]],
            self._post_data("get_thumbnail", {"uid": uid}).json(),
        )
        return response["thumbnail"]

    def upload(self, file_path: str, filename: str = "") -> str:
        """Upload file `file_path`."""
        with open(file_path, "rb") as ul_body:
            response = self._post_data(
                "upload", {"filename": filename}, ("data", ul_body, "")
            )

        if response.status_code == 202:
            raise Exception(f"Failed to upload {file_path}: {response.text}")
        j_response = cast(Dict[str, str], response.json())
        return j_response["link"]

    def shorten_url(self, url: str) -> str:
        """Shorten `url`."""
        response = cast(Dict[str, str], self._post_data("upload", {"url": url}).json())
        return response["link"]

    def delete(self, uid: str) -> None:
        """Delete uploaded item `uid`."""
        if self._post_data("delete", {"uid": uid}).status_code != 200:
            print("Failed to remove uid: " + uid)

    def edit_settings(self, settings_dict: Dict[str, str]) -> None:
        """Edit load.link settings."""
        password = getpass("What is your password? ")

        response = self._post_data(
            "edit_settings",
            {"password": password, "settings": json.dumps(settings_dict)},
        )
        if response.status_code != 200:
            print("Failed to update settings: " + response.json()["message"])

    def release_token(
        self, token_path: str = os.path.expanduser("~/.ll_token")
    ) -> None:
        """Release token at `token_path` and remove it."""
        if not token_path or not os.path.isfile(token_path):
            print(token_path + " doesn't exist to release")
            return

        if self._post_data("release_token").status_code == 200:
            os.remove(token_path)
            return

        print("Failed to release token")

    def release_all_tokens(
        self, token_path: str = os.path.expanduser("~/.ll_token")
    ) -> None:
        """Release all authentication tokens and delete `token_path`."""
        if not token_path or not os.path.isfile(token_path):
            print(token_path + " doesn't exist to release")
            return

        if self._post_data("release_all_tokens").status_code == 200:
            os.remove(token_path)
            return

        print("Failed to release all tokens")

    def prune_unused(self) -> int:
        """Prune unused links."""
        response = cast(Dict[str, int], self._post_data("prune_unused").json())
        return response["pruned"]

    def _post_data(
        self,
        action: str,
        json_dict: Optional[Dict[str, str]] = None,
        data_tuple: Optional[Tuple[str, BinaryIO, str]] = None,
    ) -> requests.Response:
        """Generic function handling all POSTs to /api endpoint."""
        payload = {"action": action}

        if json_dict:
            payload.update(json_dict)

        if "username" not in payload:
            payload["token"] = self._get_token()

        fields: Dict[str, Tuple[str, Union[BinaryIO, bytes], str]] = {
            "headers": (
                "headers",
                bytes(json.dumps(payload), "utf-8"),
                "application/json",
            )
        }

        if data_tuple:
            fields["data"] = data_tuple

        enc = MultipartEncoder(fields)
        me_monitor = MultipartEncoderMonitor(enc, _prog_cb(enc))

        response = requests.post(
            self._root_url,
            data=me_monitor,
            headers={"content-type": me_monitor.content_type},
        )

        try:
            response.raise_for_status()
        except:
            raise Exception(
                f"Error {response.status_code} with {action}: {response.text}"
            )

        return response

    def _get_token(self, token_path: str = os.path.expanduser("~/.ll_token")) -> str:
        """Check token_path for token if it exists
        or retrieve token from user input.
        """
        if os.path.isfile(token_path):
            with open(token_path, "r") as tok:
                token = tok.readline()
                if token:
                    return token

        username = input("What is your username? ")
        password = getpass("What is your password? ")

        response = self._post_data(
            "get_token", {"username": username, "password": password}
        )

        token = response.json()["token"]

        with open(token_path, "w") as tok:
            tok.write(token)

        return token


def _prog_cb(encoder: MultipartEncoder) -> Callable[[MultipartEncoderMonitor], None]:
    progress_bar = ProgressBar(expected_size=encoder.len, filled_char="=")

    def callback(
        mon: MultipartEncoderMonitor,
    ) -> None:  # pylint: disable=missing-docstring
        progress_bar.show(mon.bytes_read)

    return callback
