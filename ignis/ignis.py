"""Main file for Ignis"""
import asyncio
import logging
import msgpack
import datetime
from os.path import exists

from .entities import common

# TODO: get list of all entities, put in dataclass to show to homeassistant
# TODO: Add lazy-loading functionality for entities

# Setup logging
logging.getLogger(__name__)
# TODO: logging config


class Ignis:
    """Main class for Ignis"""
    def __init__(self, ident, access_token):
        a = common.Auth(ident, access_token)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(a.oauth_token())
        self.token = a.token

    @property
    def config(self):
        """Used to set configuration options"""
        pass

    async def get_all(self):
        pass

# NOTE: Experimental feature, no idea if it will even increase performance
# TODO: Maybe for the cache refreshing function, get a hash of file and new data
# and compare. If hashes are different, then write data.
class EntityCache:
    """
    Create and manage a cache containing a list of entities, aiding in part
    with the lazy-loading aspect of this library
    """
    def __init__(self, entity_type):
        self.cache_exists = True if exists(".entity_cache/") is True else False
        self.entity_type = entity_type

    async def create_cache(self):
        """Create a cache containing entities"""
        # Tell Entity class about entity type
        e = common.Entity()
        e.entity_type = self.entity_type
        if self.cache_exists is True:
            logging.warn("Cache already exists! Overwriting")
        entities = {"entities": await e.get_list(), "date": datetime.datetime.now()}
        data = msgpack.packb(entities)
        cache = open(f".entity_cache/{self.entity_type}", "w")
        cache.write(data)
        logging.info("Cache has been created!")
        cache.close()


    async def refresh_cache(self):
        """Refresh the entity cache"""
        if self.cache_exists is False:
            logging.error("Cache does not exist! Skipping")
            pass
