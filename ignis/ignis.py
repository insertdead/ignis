"""Main file for Ignis"""
import asyncio
import logging

from .entities import common, minisplits, puck, rooms, structure, vent

# TODO: get list of all entities, put in dataclass to show to homeassistant

# Setup logging
logging.getLogger(__name__)
# TODO: logging config


class Ignis:
    def __init__(self, ident, access_token, **kwargs):
        self.headers = kwargs.get("headers")
        a = common.Auth(ident, access_token)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(a.oauth_token())
        self.token = a.token
