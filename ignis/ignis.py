"""Main file for Ignis"""
import logging
from ignis.entities import (
    common,
    minisplits,
    puck,
    rooms,
    structure,
    vent
)
# TODO: get list of all entities, put in dataclass to show to homeassistant

# Setup logging
logging.getLogger(__name__)
# TODO: logging config

class Ignis:
    def __init__(self, ident, access_token, **kwargs):
        self.ident = ident
        self.access_token = access_token
        self.headers = kwargs.get("headers")

    async def init(self):
        a = common.Auth(self.ident, self.access_token)
        self.token = await a.oauth_token()
