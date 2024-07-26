"""Config for calendar sync."""
from __future__ import annotations

import copy
import logging
import os
from typing import TYPE_CHECKING, Any

import yaml

from .exceptions import ConfigDoesNotExistException, InvalidConfigException

if TYPE_CHECKING:
    from pathlib import Path


logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    'google_api_path': 'api_credentials.json',
    'google_token_path': 'token.json',
    'moodle_session_id': None,
    'moodle_cred_path': 'moodle_credentials.json',
    'login_with_token': False,
    'num_of_months': 6,
}


def load_config(config_file: Path | str | None = None):
    """Load config from file."""
    # if config_file is None, use default config
    if config_file is None:
        logger.debug('No config file specified, using default config.')
        return copy.copy(DEFAULT_CONFIG)

    # otherwise, load config from file
    if not os.path.exists(config_file):
        msg = f'File `{config_file}` does not exist.'
        raise ConfigDoesNotExistException(msg)

    logger.debug('Loading config from %s.', config_file)
    with open(config_file, 'r', encoding='utf-8') as f:
        try:
            yaml_dict = yaml.safe_load(f)
        except yaml.YAMLError as e:
            msg = f'Unable to parse YAML file `{config_file}`'
            raise InvalidConfigException(msg) from e

        if not isinstance(yaml_dict, dict):
            msg = f'Top-level element of YAML file `{config_file}` should be an object.'
            raise InvalidConfigException(msg)

    return merge_config(DEFAULT_CONFIG, yaml_dict)


def merge_config(default: dict[str, Any], overwrite: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge two dictionaries."""
    new_config = copy.deepcopy(default)
    for key, value in overwrite.items():
        if isinstance(value, dict):
            new_config[key] = merge_config(default.get(key, {}), value)
        else:
            new_config[key] = value

    return new_config
