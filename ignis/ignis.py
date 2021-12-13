"""Main module for Ignis"""
import asyncio
import datetime
import logging
from enum import Enum, unique
from os.path import exists
from typing import Optional

import msgpack
from aiohttp.client import ClientSession

from .entities import Entity
from .utils import Util

HOST = "https://api.flair.co"
SCOPE = "thermostats.view+structures.view+structures.edit"
DEFAULT_HEADERS = {
    "Accept": "application/vnd.api+json",
    "Content-Type": "application/json",
}


@unique
class Entities(Enum):
    """Enum of all implemented entity types found in the API, with a value corresponding to their name in the API"""

    USER = "users"
    STRUCTURE = "structures"
    ROOM = "rooms"
    PUCK = "pucks"
    VENT = "vents"
    MINISPLIT = "hvac-units"
    THERMOSTAT = "thermostats"


# FIXME: Rename
class Ignis:
    """Main class for Ignis
    Setup is handled by the `__setup` private method with some of the class args, retrieving an access token and setting up logging.
    Feed `Ignis` instance to Entity instances to allow them to connect to the API.
    """

    def __init__(self, ident: str, access_token: str, log_level="DEBUG", **kwargs):
        self.lazy_mode: bool = kwargs.get("lazy_mode", True)
        scope: Optional[str] = kwargs.get("scope")
        self.scope: str = f"{SCOPE}+{scope}"
        self.__legacy_oauth: bool = kwargs.get("legacy_oauth", False)
        self.__headers: dict = kwargs.get("headers", DEFAULT_HEADERS)
        asyncio.run(self.__setup(ident, access_token, log_level))

    async def __setup(self, ident, access_token, log_level):
        """Offloading boiler to another method to clear up `__init__`"""
        # Setup logging
        logging.getLogger(__name__)
        logging.basicConfig(
            format="%(asctime)s - %(module)s %(levelname)s: %(message)s",
            level=log_level,
        )

        # Get credentials
        logging.info("Retrieving credentials from API with supplied authentication")
        await self.__auth(ident, access_token)

    async def __auth(self, ident, access_token):
        u = Util()
        match self.__legacy_oauth:
            case False:  # Use OAuth 2.0 (Recommended)
                url = await u.create_url("/oauth2/token")
                credentials = {
                    "client_id": ident,
                    "client_secret": access_token,
                    "scope": self.scope,
                }
                async with ClientSession() as session:
                    async with session.post(
                        url, params=credentials, headers=self.headers
                    ) as resp:
                        json = await resp.json()
                        token = json.get("access_token")
                        if resp.status is not 200:
                            # FIXME: Maybe raise an exception instead or retry
                            logging.error(
                                f"""Error code received from HTTP response: {resp.status}\n
                                HTTP Response:\n{resp.text}"""
                            )
                        return token

            case True:  # Use OAuth 1.0
                url = await u.create_url("/oauth/token")
                raise NotImplementedError()

    @property
    def lazy_mode(self):  # type: ignore
        """Whether or not to lazily evaluate.
        Default is `True` as lazy evaluation will generally provide a better user experience
        """
        logging.info(
            f"Getter called for lazy_mode. Lazy evaluation is currently: {self.__lazy_mode}"
        )
        return self.__lazy_mode

    @lazy_mode.setter
    def lazy_mode(self, new_mode):  # type: ignore
        logging.info(
            f"Setter called for lazy_mode. Lazy evaluation is currently: {self.__lazy_mode}"
        )
        self.__lazy_mode = new_mode

    @property
    def headers(self):
        """Default headers to use.
        Should not be changed, only read
        """
        logging.info(
            f"Getter called for headers. Headers are currently: {self.__headers}"
        )

    async def refresh(self):
        """Refresh credentials"""
        raise NotImplementedError()


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
        raise NotImplementedError("Not working on this right now, come back later! :-)")

    async def create_cache(self):
        """Create a cache containing entities"""
        # Tell Entity class about entity type
        # e = common.Entity()
        e = NotImplemented
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
