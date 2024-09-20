"""
Runs main.sync with default config.
"""
import sys

from . import config, main

config_path = None

if len(sys.argv) > 1:
    config_path = sys.argv[1]

main.sync(config=config.load_config(config_path))
