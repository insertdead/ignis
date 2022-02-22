"""Main module for Ignis."""
import asyncio
import logging
import secrets
import string
from abc import ABC, abstractmethod
from tkinter import W
from types import TracebackType
from typing import Optional, Type

import msgpack
from aiohttp.client import ClientSession

from .utils import DEFAULT_HEADERS, SCOPE, APIError, Unreachable, Util


async def gen_oauth_state() -> str:
    """Generate a state code for OAuth."""
    alphabet = string.ascii_letters + string.digits
    state = "".join(secrets.choice(alphabet) for _ in range(10))
    return state


# NOTE: I assume it is not too inefficient to just initiate a new ClientSession
#   for every operation, and it would solve many issues related to the event
#   loop. If it does indeed pose a performance issue, I will patch together a
#   hack to fix this
class AbstractConfig(ABC):
    """Setup class for Ignis.

    In most cases, this class by itself should be usable, but should one want to
    use authorization, they must provide a subclass providing the code that will
    enable getting the code and opening a browser along with all those shenanigans,
    as methods to do this can vary wildly depending on the use-case and environment.
    This package comes with two pre-made subclasses that implement authorization
    for homeassistant and locally (if you plan on using this in a graphical desktop environment).

    Setup is handled by the `__setup` private method with some of the class args,
    retrieving an access token and setting up logging. Feed `Config` instance to
    Entity instances to allow them to connect to the API.

    NOTE: This class should only have *one* instance per user/account.
    """

    def __init__(
        self,
        ident: str,
        access_token: str,
        scope: str,
        log_level: str = "DEBUG",
        **kwargs,
    ):
        """Set some parameters and set up the instance."""
        self.access_token = access_token
        self.authorization = kwargs.get("authorization", False)
        self.headers = kwargs.get("headers", DEFAULT_HEADERS)
        self.ident = ident
        self.log_level = log_level
        self.legacy_oauth = kwargs.get("legacy_oauth", False)
        self.scope = scope
        self.__lazy_mode = kwargs.get("lazy_mode", True)
        asyncio.run(self._init())

    @abstractmethod
    async def _init(self):
        # Setup logging
        logging.getLogger(__name__)
        logging.basicConfig(
            format="%(asctime)s - %(module)s %(levelname)s: %(message)s",
            level=self.log_level,
        )

        # Initialize ClientSession and get credentials
        self.websession = ClientSession()
        logging.info("Retrieving credentials from API with supplied authentication")
        self.token: str = await self.__authentication(self.ident, self.access_token)

    async def __authentication(self, ident: str, access_token: str) -> str:
        """Private method to retrieve credentials from the API, using the authentication method."""
        u = Util()
        credentials = {
            "client_id": ident,
            "client_secret": access_token,
            "scope": self.scope,
            "grant_type": "client_credentials",
        }

        if self.legacy_oauth == False:  # Use OAuth 2.0 (Recommended)
            url = await u.create_url("/oauth2/token")
            resp = await self.websession.post(url, data=credentials)
            json: dict = await resp.json()
            if resp.status != 200:
                print(credentials)
                raise APIError(
                    f"Error code received from HTTP response ({resp.status}). Maybe incorrect secret and/or ID provided?",
                    await resp.json(),
                )
            token: str = json["access_token"]
            return token

        elif self.legacy_oauth == True:
            url = await u.create_url("/oauth/token")
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            credentials["grant_type"] = "password"

            resp = await self.websession.post(url, params=credentials, headers=headers)
            json: dict = await resp.json()
            if resp.status != 200:
                raise APIError(
                    f"Error code received from HTTP response ({resp.status}). Maybe incorrect secret and/or ID provided?",
                    str(json),
                )
            token: str = json["access_token"]
            return token
        else:
            raise Unreachable()

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

    @abstractmethod
    async def refresh(self):
        """Refresh credentials.

        This is usually done automatically on a timer, but can be run on command
        if needed.
        """
        pass

    @abstractmethod
    async def stop(self):
        """Stop all tasks started by this class cleanly."""
        # await self.websession.close()

    async def __aenter__(self) -> "AbstractConfig":
        await self._init()
        return self

    async def __aexit__(
        self,
        exc_t: Type[BaseException],
        exc_v: BaseException,
        exc_tb: TracebackType,
    ) -> None:
        await self.stop()
        return


class HassConfig(AbstractConfig):
    """Prepackaged class to be used by homeassistant and its OAuth facilities.

    Only really meant to be an example of sorts, however it's used in my
    homeassistant integration, for those who also want to see an example use of such a class
    """

    def __init__(
        self,
        websession: ClientSession,
        token_manager,
        log_level: str = "DEBUG",
        **kwargs,
    ):
        """Set some parameters and set up the instance."""
        self.lazy_mode: bool = kwargs.get("lazy_mode", True)
        self.websession: ClientSession = websession
        self.token_manager = token_manager
        scope: Optional[str] = kwargs.get("scope")
        self.scope: str = f"{SCOPE}+{scope}"
        self.__legacy_oauth: bool = kwargs.get("legacy_oauth", False)
        self.authorization: bool = (
            False if self.__legacy_oauth is True else kwargs.get("authorization", False)
        )
        self.__headers: dict = kwargs.get("headers", DEFAULT_HEADERS)
        asyncio.run(self.__setup(log_level))

    async def __setup(self, log_level):
        """Offloading boiler to another method to clear up `__init__`."""
        # Setup logging
        logging.getLogger(__name__)
        logging.basicConfig(
            format="%(asctime)s - %(module)s %(levelname)s: %(message)s",
            level=log_level,
        )

        # Get credentials
        logging.info("Retrieving credentials from API with supplied authentication")
        if self.token_manager.is_valid():
            self.token = self.token_manager.access_token
            return

        await self.token_manager.fetch_access_token()
        await self.token_manager.save_access_token()

        self.token = self.token_manager.access_token
        return

    async def refresh(self):
        """Refresh credentials.

        This is usually done automatically on a timer, but can be run on command
        if needed.
        """
        if self.token_manager.is_valid():
            logging.warn("Token still valid! Skipping.")
            pass

        await self.token_manager.refresh_token()
        await self.token_manager.save_access_token()

        self.token = self.token_manager.access_token


class BasicConfig(AbstractConfig):
    """Basic config class, used primarily for testing.

    It is highly recommended you create your own config class if you are going
    to use this in your own project, and tailor it to your own needs.
    """

    def __init__(
        self,
        ident: str,
        access_token: str,
        scope: str,
        log_level: str = "DEBUG",
        **kwargs,
    ):
        super().__init__(ident, access_token, scope, log_level, **kwargs)

    async def _init(self):
        await super()._init()
        self._refresh_task = asyncio.create_task(
            self.refresh(self.ident, self.access_token)
        )

    async def refresh(self, ident, access_token):
        """Refresh the token every hour."""
        try:
            while True:
                await asyncio.sleep(3600)
                await super().__authentication(ident, access_token)
        except asyncio.CancelledError:
            logging.info("Request to stop refresh task. Stopping..")
            return

    async def stop(self):
        self._refresh_task.cancel()
        return await super().stop()

    async def __aenter__(self) -> "AbstractConfig":
        return await super().__aenter__()

    async def __aexit__(
        self, exc_t: Type[BaseException], exc_v: BaseException, exc_tb: TracebackType
    ) -> None:
        await self.stop()
        return await super().__aexit__(exc_t, exc_v, exc_tb)


# FIXME: Use redis instead because of its speed and it actually being a database
# TODO: Add to project readme that *if* redis features are to be used, the redis server must of course be installed
# class EntityCache:
#     """Create and manage a cache containing a list of entities.

#     This will aid the lazy-loading aspect of this library
#     """

#     def __init__(self, entity_type):
#         """Check if the cache exists and get the entity type."""
#         self.cache_exists = True if exists(".entity_cache/") is True else False
#         self.entity_type = entity_type
#         raise NotImplementedError("Not working on this right now, come back later! :-)")

#     async def create_cache(self):
#         """Create a cache containing entities."""
#         # Tell Entity class about entity type
#         # e = common.Entity()
#         e = NotImplemented
#         e.entity_type = self.entity_type
#         if self.cache_exists is True:
#             logging.warn("Cache already exists! Overwriting")
#         entities = {"entities": await e.get_list(), "date": datetime.datetime.now()}
#         data = msgpack.packb(entities)
#         cache = open(f".entity_cache/{self.entity_type}", "w")
#         cache.write(data)
#         logging.info("Cache has been created!")
#         cache.close()

#     async def refresh_cache(self):
#         """Refresh the entity cache."""
#         if self.cache_exists is False:
#             logging.error("Cache does not exist! Skipping")
#             pass
