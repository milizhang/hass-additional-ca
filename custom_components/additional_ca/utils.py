"""Python functions for Additional CA."""

import logging
import os
import random
import shutil
import string
import subprocess
import certifi

from .const import CA_SYSPATH, UPDATE_CA_SYSCMD

_LOGGER = logging.getLogger(__name__)


def remove_additional_ca(ca_filename: str) -> bool:
    os.remove(os.path.join(CA_SYSPATH, ca_filename))
    return True


def remove_all_additional_ca(additional_ca_store: dict) -> bool:
    """
    Clean current user's additional CA.
    Do not remove CA cert file not owned by user.
    -> compare  with data stored in .storage (see homeassistnat.helpers.storage)
    """
    for filename in os.listdir(CA_SYSPATH):
        for _, cafile in additional_ca_store.items():
            if filename == cafile:
                file_path = os.path.join(CA_SYSPATH, filename)
                try:
                    os.unlink(file_path)
                except Exception as err:
                    _LOGGER.warning(f"Failed to delete {file_path} Reason: {err}")
                    return False
    return True

def append_ca_to_certifi(ca_src_fullpath: str):
    ca_file = os.path.basename(ca_src_fullpath)
    certifi_bundle_file = certifi.where()
    certifi_bundle = open(certifi_bundle_file, "a")
    ca_file = open(ca_src_fullpath, "r")
    certifi_bundle.write("\n")
    certifi_bundle.write(ca_file.read())
    ca_file.close()
    certifi_bundle.close()

def copy_ca_to_system(ca_src_fullpath: str) -> str:
    ca_file = os.path.basename(ca_src_fullpath)
    unique_ca_name = f"{generate_uid()}_{ca_file}"
    shutil.copy(ca_src_fullpath, os.path.join(CA_SYSPATH, unique_ca_name))
    return unique_ca_name


def update_system_ca() -> bool:
    cmd = [UPDATE_CA_SYSCMD]
    error_prefix = f"'{UPDATE_CA_SYSCMD}' returned an error -> "
    try:
        # status = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
        status = subprocess.run(cmd, capture_output=True, check=True)
    except subprocess.CalledProcessError as err:
        _LOGGER.warning(f"{error_prefix}{str(err)}")
        raise
    except Exception as err:
        _LOGGER.warning(f"{error_prefix}{str(err)}")
        raise

    if status.stderr:
        _LOGGER.warning(f"{error_prefix}{status.stderr.decode().rstrip()}")
        raise Exception

    return True


def generate_uid(length: int = 8) -> str:
    letters = string.digits
    return "".join(random.choice(letters) for _ in range(length))
