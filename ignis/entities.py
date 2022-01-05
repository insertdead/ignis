"""Common code between all entities."""
import asyncio
import logging
from abc import ABC, ABCMeta, abstractmethod
from typing import Optional

from aiohttp import ClientSession
from attr import attr

from ignis.ignis import AbstractConfig, Entities

from .utils import APIError, EntityAttributeError, EntityError, Unreachable, Util

HOST = "https://api.flair.co"
DEFAULT_HEADERS = {
    "Accept": "application/vnd.api+json",
    "Content-Type": "application/json",
}


async def get(token: str, entity_type: Entities, entity_id: str) -> dict:
    """Retrieve an entity from the API.

    This should normally be never used anywhere outside the library, but may be used when creating a new entity if needed.
    """
    u = Util()

    url: str = await u.entity_url(entity_type, entity_id)
    headers = DEFAULT_HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"

    logging.info(
        f'`get()` function called for entity "{entity_id}" of type {entity_type.name}.'
    )

    async with ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status is not 200:
                raise APIError(
                    f"Error code {resp.status} returned from API", str(resp.text)
                )
            json = await resp.json()

    if json:
        return json
    else:
        raise Unreachable()


async def get_list(
    websession: ClientSession, token: str, entity_type: Entities
) -> dict:
    """Get a list of entities of a certain type."""
    u = Util()

    url: str = await u.create_url(f"/api/{entity_type.name}")
    headers = DEFAULT_HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"

    async with websession.get(url, headers=headers) as resp:
        if resp.status is not 200:
            raise APIError(
                f"Error code {resp.status} returned from API. Check the provided token!",
                str(resp.text),
            )
        json = await resp.json()

    if json:
        return json
    else:
        raise Unreachable()


async def id_from_name(
    websession: ClientSession,
    token: str,
    entity_type: Entities,
    attributes: dict,
    name: str,
) -> str:
    """Get entity ID from its name."""
    # TODO: Once redis database functionality is enabled, add a case statement that goes through the methods of finding the id
    entity_id = attributes.get("id")
    if entity_id is None:
        entity_list = await get_list(websession, token, entity_type)
        entity_num = next(
            (
                i
                for i, item in enumerate(entity_list["data"])
                if item["attributes"]["name"] is name
            ),
            None,
        )
        entity_id = entity_list[entity_num]["id"]

    logging.info(f"Got id `{entity_id}` from name `{name}`")
    return entity_id


async def control(
    websession: ClientSession,
    token: str,
    entity_id: str,
    entity_type: Entities,
    attributes: dict,
    **kwargs,
):
    """Control an entity via POST http requests."""
    u = Util()
    url: str = await u.entity_url(entity_type, entity_id)
    additional_data: dict = kwargs.get("additional_data", {})

    headers = DEFAULT_HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"

    body = {}
    body["data"] = additional_data
    body["data"]["type"] = entity_type.name
    body["data"]["attributes"] = attributes

    async with websession.post(url, data=body, headers=headers) as resp:
        if resp.status is not 200:
            raise APIError(
                f"Error code {resp.status} returned from API. Check the provided token!",
                str(resp.text),
            )
        json = await resp.json()

    if json:
        return json
    else:
        raise Unreachable()


class AbstractEntity(ABC):
    """Superclass of all Entity classes.

    Can also be used to add a custom entity type not implemented in the library with relative ease.
    """

    def __init__(
        self, config: AbstractConfig, entity_type: Entities, **kwargs: Optional[str]
    ):
        """Prepare some variables and get boilerplate out of the way."""
        self.config: AbstractConfig = config
        self.entity_type: Entities = entity_type
        self.__name: Optional[str] = kwargs.get("name")
        self.__entity_id: Optional[str] = kwargs.get("entity_id")
        self.__attributes: dict = {}
        if self.__name or self.__entity_id is None:
            raise EntityError("Either `name` or `entity_id` must be set")

    @abstractmethod
    async def control(self):
        """Modify the entity's attributes."""

    @property
    def name(self) -> str:
        """Getter for the entity name.

        Here to make sure that it is not called if it doesn't exist in a safe way.
        """
        # TODO: add reverse of `id_from_name` and get name from id. Shouldn't be *too* difficult.
        logging.debug(f"Getter called for name.")
        if self.__name is None:
            logging.error("`name` does not exist! Skipping")
            pass
        # type here has been ignored as a type check is placed in the `__init__` method and in the previous `if` statement
        return self.__name  # type: ignore

    @property
    def entity_id(self) -> str:
        """Getter for the entity ID.

        Here to retrieve the entity ID if only the name has been provided, for the end-user's convenience.
        """
        logging.debug(
            f"Getter called for entity_id. entity_id is currently: {self.__entity_id}"
        )
        if self.__entity_id is None and self.__name is not None:
            logging.warn("entity_id does not exist, retrieving it from API")
            entity_id = asyncio.run(
                id_from_name(
                    self.config.websession,
                    self.config.token,
                    self.entity_type,
                    self.attributes,
                    self.name,
                )
            )
        else:
            raise Unreachable()

        return entity_id

    @property
    def attributes(self) -> dict:
        """Entity attributes, structured more or less as found in the API."""
        # TODO: Get attributes working
        exists = "not" if self.__attributes is None else ""
        logging.debug(
            f"Getter called for attributes. attributes do {exists} exist for this entity"
        )
        self.__attributes = (
            self.__attributes
            if not {}
            else asyncio.run(get(self.config.token, self.entity_type, self.entity_id))
        )
        return self.__attributes


class User(AbstractEntity):
    """Entity Class for the users entity type."""

    async def control(self):
        """Control the user entity.

        Notable settings include:
            - `name`: username (read-only)
            - `email`: user's email (read-only)
            - various preferences, such as the temperature scale, the default temperature preference, etc.
        """
