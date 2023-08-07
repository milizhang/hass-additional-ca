"""The Additional CA integration."""

from __future__ import annotations

import logging
import os

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import CONFIG_SUBDIR, DOMAIN
from .storage import AdditionalCAStore
from .utils import (
    copy_ca_to_system,
    remove_additional_ca,
    remove_all_additional_ca,
    update_system_ca,
    append_ca_to_certifi,
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({DOMAIN: {cv.string: cv.string}}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Additional CA component."""

    config_path = hass.config.path(CONFIG_SUBDIR)

    if not os.path.isdir(config_path):
        _LOGGER.warning(f"Folder {CONFIG_SUBDIR} not found in configuration folder.")
        return False

    try:
        store = AdditionalCAStore(hass)
        await update_ca_certificates(hass, config, store)
    except:
        _LOGGER.warning("Additional CA setup has been interrupted.")
        raise

    return True


async def update_ca_certificates(hass: HomeAssistant, config: ConfigType, store: AdditionalCAStore) -> bool:
    """Update CA certificates at system level."""

    conf = config.get(DOMAIN)

    config_path = hass.config.path(CONFIG_SUBDIR)

    try:
        os.path.isdir(config_path)
    except:
        _LOGGER.warning(f"Folder {CONFIG_SUBDIR} not found in configuration folder.")
        raise

    additional_ca_data = await store.load_storage_data()

    if additional_ca_data is None:
        additional_ca_data = {}

    # clean all current additional CA
    try:
        remove_all_additional_ca(additional_ca_data)
    except:
        raise

    # reset system CA
    try:
        update_system_ca()
    except:
        raise

    _LOGGER.info("Ready.")

    # copy custom additional CA to system
    new_additional_ca_data = {}
    for ca_idname, ca_filepath in conf.items():
        additional_ca_fullpath = os.path.join(config_path, ca_filepath)

        # TODO: add certificate format checking

        if not os.path.exists(additional_ca_fullpath):
            _LOGGER.warning(f"{ca_idname}: {ca_filepath} not found.")
            continue

        if os.path.isfile(additional_ca_fullpath):
            append_ca_to_certifi(additional_ca_fullpath)
            ca_uname = copy_ca_to_system(additional_ca_fullpath)
            try:
                update_system_ca()
            except:
                _LOGGER.warning(f"Unable to load {ca_idname} ({ca_filepath}) into system CA. See previous errors.")
                remove_additional_ca(ca_uname)
                update_system_ca()
            else:
                # store CA infos for persistence across reboots in /config/.storage/
                new_additional_ca_data[ca_idname] = ca_uname
                await store.save_storage_data(new_additional_ca_data)
                _LOGGER.info(f"{ca_idname} ({ca_filepath}) -> loaded.")

        elif os.path.isdir(additional_ca_fullpath):
            _LOGGER.warning(f"{additional_ca_fullpath} is a not a CA file.")

    return True
