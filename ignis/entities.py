"""Common code between all entities."""
import asyncio
import datetime
import logging
from abc import ABC
from typing import Optional

from aiohttp import ClientSession

from ignis.ignis import AbstractConfig, Entities

from .utils import APIError, EntityAttributeError, EntityError, Unreachable, Util

# from attr import attr


HOST = "https://api.flair.co"
DEFAULT_HEADERS = {
    "Accept": "application/vnd.api+json",
    "Content-Type": "application/json",
}


async def get(
    websession: ClientSession, token: str, entity_type: Entities, entity_id: str
) -> dict:
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

    async with websession.get(url, headers=headers) as resp:
        if resp.status != 200:
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
        if resp.status != 200:
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
    entity: dict,
    name: str,
) -> str:
    """Get entity ID from its name."""
    # TODO: Once redis database functionality is enabled, add a case statement that goes through the methods of finding the id
    entity_id = entity.get("id")
    if entity_id is None:
        entity_list = await get_list(websession, token, entity_type)
        entity_num = next(
            (
                i
                for i, item in enumerate(entity_list["data"])
                if item["attributes"]["name"] == name
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
    attributes: Optional[dict],
    **kwargs,
):
    """Control an entity via POST http requests."""
    u = Util()
    url: str = await u.entity_url(entity_type, entity_id)
    additional_data: dict = kwargs.get("additional_data", {})

    headers = DEFAULT_HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"

    if attributes == None and additional_data == {}:
        raise EntityAttributeError(
            "Missing attributes and additional data! At least one must be set"
        )

    body = {}
    body["data"] = additional_data
    body["data"]["type"] = entity_type.name
    body["data"]["attributes"] = attributes

    async with websession.post(url, data=body, headers=headers) as resp:
        if resp.status != 200:
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
        self.name: Optional[str] = kwargs.get("name")
        self.entity_id: Optional[str] = kwargs.get("entity_id")
        self.entity: dict = asyncio.run(self.__setup())
        if self.name and self.entity_id == None:
            raise EntityError("Either `name` or `entity_id` must be set")
        # TODO: refactor to get entity info only once

    async def __setup(self) -> dict:
        logging.debug(f"Setting up new {self.entity_type.name}")
        # Get id if it isn't provided, but name is
        if self.entity_id == None:
            logging.warn("entity_id does not exist, retrieving it from API")
            self.entity_id = await id_from_name(
                self.config.websession,
                self.config.token,
                self.entity_type,
                self.name,  # type: ignore
            )
        else:
            raise Unreachable()

        entity = await get(
            self.config.websession, self.config.token, self.entity_type, self.entity_id
        )

        if self.name == None:
            logging.info("name does not exist, retriving it from API")
            try:
                self.name = entity["attributes"]["name"]
            except KeyError:
                raise EntityAttributeError(
                    "Entity attribute `name` could not be found. Create an issue at <https://github.com/insertdead/ignis>"
                )

        return entity


class User(AbstractEntity):
    """Entity Class for the users entity type."""

    def __init__(self, config: AbstractConfig, **kwargs: Optional[str]):
        super().__init__(config, Entities.USER, **kwargs)

    async def default_temperature_preference(
        self, temp: Optional[int]
    ) -> Optional[int]:
        if temp == None:
            try:
                new_temp = int(self.entity["data"]["default-temperature-preference-c"])
                # TODO: redis cache
            except ValueError:
                logging.error(
                    "Data received from API could not be parsed into int! Skipping"
                )
                return
        else:
            new_temp = temp

        body = {"default-temperature-preference-c": str(temp)}
        logging.info(f"Default temperature set to {temp} degrees Celcius!")
        # type check ignored due to checks that would have already set id as a
        #  valid id
        await control(
            self.config.websession,
            self.config.token,
            self.entity_id,  # type: ignore
            self.entity_type,
            None,
            additional_data=body,
        )
        return new_temp


class Structure(AbstractEntity):
    """Entity class for the structures entity type.

    Contains most settings useful for the user. Also contains a list of all available rooms.
    """

    def __init__(self, config: AbstractConfig, **kwargs: Optional[str]):
        super().__init__(config, Entities.STRUCTURE, **kwargs)

    async def temperature_scale(self) -> bool:
        scale = True if self.entity["attributes"]["temperature-scale"] == "C" else False
        return scale

    async def home(self, is_home: bool) -> bool:
        raise NotImplementedError

    async def structure_heat_cool_mode(self) -> str:
        raise NotImplementedError

    async def mode_toggle(self) -> str:
        raise NotImplementedError

    async def list_rooms(self) -> list[dict]:
        raise NotImplementedError


class Room(AbstractEntity):
    """Entity class for the rooms entity type.

    Similarly to structures, it contains settings pertinent to most users, but
    on a room-by-room basis.
    """

    async def set_point_c(self, temp: Optional[int]) -> int:
        raise NotImplementedError

    async def active(self, toggle: bool) -> bool:
        raise NotImplementedError

    async def current_temperature_c(self) -> float:
        raise NotImplementedError

    async def current_humidity(self) -> int:
        raise NotImplementedError


class Puck(AbstractEntity):
    """Entity class for the pucks entity type.

    This puck is read-only, and only used for displaying statistics.
    """

    async def created_at(self) -> datetime.datetime:
        raise NotImplementedError

    # async def
