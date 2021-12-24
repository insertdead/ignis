"""Main module for Ignis."""
import asyncio
import datetime
import logging
from enum import Enum, unique
from os.path import exists
from typing import Optional

import msgpack
from aiohttp.client import ClientSession

from .entities import Entity
from .utils import APIError, Util

HOST = "https://api.flair.co"
SCOPE = "thermostats.view+structures.view+structures.edit"
DEFAULT_HEADERS = {
    "Accept": "application/vnd.api+json",
    "Content-Type": "application/json",
}


@unique
class Entities(Enum):
    """Enum of all implemented entity types found in the API, with a value corresponding to their name in the API.

    If you plan to add an entity type, you *must* add it to this enum.
    """

    USER = "users"
    STRUCTURE = "structures"
    ROOM = "rooms"
    PUCK = "pucks"
    VENT = "vents"
    MINISPLIT = "hvac-units"
    THERMOSTAT = "thermostats"


class Config:
    """Main class for Ignis.

    Setup is handled by the `__setup` private method with some of the class args, retrieving an access token and setting up logging.
    Feed `Ignis` instance to Entity instances to allow them to connect to the API.

    NOTE: This class should only have *one* instance per user/account.
    """

    def __init__(
        self, ident: str, access_token: str, log_level: str = "DEBUG", **kwargs
    ):
        """Set some parameters and set up the instance."""
        self.lazy_mode: bool = kwargs.get("lazy_mode", True)
        scope: Optional[str] = kwargs.get("scope")
        self.scope: str = f"{SCOPE}+{scope}"
        self.__legacy_oauth: bool = kwargs.get("legacy_oauth", False)
        self.__headers: dict = kwargs.get("headers", DEFAULT_HEADERS)
        asyncio.run(self.__setup(ident, access_token, log_level))

    async def __setup(self, ident, access_token, log_level):
        """Offloading boiler to another method to clear up `__init__`."""
        # Setup logging
        logging.getLogger(__name__)
        logging.basicConfig(
            format="%(asctime)s - %(module)s %(levelname)s: %(message)s",
            level=log_level,
        )

        # Get credentials
        logging.info("Retrieving credentials from API with supplied authentication")
        self.token: str = await self.__authentication(ident, access_token)

    # TODO: add method for authenticating via authorization method
    async def __authentication(self, ident: str, access_token: str) -> str:
        """Private method to retrieve credentials from the API, using the authentication method."""
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
                            raise APIError(
                                f"Error code received from HTTP response ({resp.status}). Maybe incorrect secret and/or ID provided?",
                                str(resp.text),
                            )
                        return token

            case True:  # Use OAuth 1.0
                url = await u.create_url("/oauth/token")
                raise NotImplementedError(
                    "OAuth 1.0 not yet supported! Check back later :)"
                )

        async def __authorization(self, application_id: str, return_uri: str) -> str:
            """Use the authorization workflow for OAuth.

            Note that only OAuth 2.0 is supported for this workflow.
            """
            raise NotImplementedError(
                "Authorization is not yet supported! Check back later :)"
            )

    @property
    def lazy_mode(self) -> bool:  # type: ignore
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
    def headers(self) -> dict:
        """Headers used by default.

        Should not be changed, only read
        """
        logging.info(
            f"Getter called for headers. Headers are currently: {self.__headers}"
        )

        return self.__headers

    async def refresh(self):
        """Refresh credentials.

        This is usually done automatically on a timer, but can be manually run if needed
        """
        raise NotImplementedError()


# FIXME: Use redis instead because of its speed and it actually being a database
# TODO: Add to project readme that *if* redis features are to be used, the redis server must of course be installed
class EntityCache:
    """Create and manage a cache containing a list of entities.

    This will aid the lazy-loading aspect of this library
    """

    def __init__(self, entity_type):
        """Check if the cache exists and get the entity type."""
        self.cache_exists = True if exists(".entity_cache/") is True else False
        self.entity_type = entity_type
        raise NotImplementedError("Not working on this right now, come back later! :-)")

    async def create_cache(self):
        """Create a cache containing entities."""
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
        """Refresh the entity cache."""
        if self.cache_exists is False:
            logging.error("Cache does not exist! Skipping")
            pass
