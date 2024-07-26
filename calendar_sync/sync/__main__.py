"""
Runs main.sync with default config.
"""
from . import config, main

main.sync(config=config.load_config())
