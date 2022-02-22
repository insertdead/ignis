"""Common code between all entities."""
import asyncio
import datetime
import logging
from abc import ABC
from typing import Optional

from aiohttp import ClientSession

from ignis.ignis import AbstractConfig

from .utils import (
    APIError,
    Entities,
    EntityAttributeError,
    EntityError,
    Unreachable,
    Util,
)

HOST = "https://api.flair.co"
DEFAULT_HEADERS = {
    "Accept": "application/vnd.api+json",
    "Content-Type": "application/json",
}


async def get(
    websession: ClientSession, token: str, entity_typ: Entities, entity_id: str
) -> dict:
    """Retrieve an entity from the API.

    This should normally be never used anywhere outside the library, but may be
    used when creating a new entity if needed.
    """
    u = Util()

    url: str = await u.entity_url(entity_typ, entity_id)
    headers = DEFAULT_HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"

    logging.info(
        f'`get()` function called for entity "{entity_id}" of type {entity_typ.value}.'
    )

    resp = await websession.get(url, headers=headers)
    if resp.status != 200:
        raise APIError(f"Error code {resp.status} returned from API", await resp.json())
    json = await resp.json()

    if json:
        return json
    else:
        raise Unreachable()


async def get_list(websession: ClientSession, token: str, entity_typ: Entities) -> dict:
    """Get a list of entities of a certain type."""
    u = Util()

    url: str = await u.create_url(f"/api/{entity_typ.value}")
    headers = DEFAULT_HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"

    resp = await websession.get(url, headers=headers)
    json = await resp.json()
    if resp.status != 200:
        raise APIError(
            f"Error code {resp.status} returned from API. Check the provided token!",
            json,
        )

    if json:
        return json
    else:
        raise Unreachable()


async def get_rel(
    websession: ClientSession, token: str, rel: tuple[Entities, Entities]
) -> list[str]:
    """Get the relationships between one entity type and another type."""
    raise NotImplementedError


async def id_from_name(
    websession: ClientSession,
    token: str,
    entity_typ: Entities,
    entity: dict,
    name: str,
) -> str:
    """Get entity ID from its name."""
    # TODO: Once redis database functionality is enabled, add a case statement that goes through the methods of finding the id
    entity_id = entity.get("id")
    if entity_id is None:
        entity_list = await get_list(websession, token, entity_typ)
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
    config: AbstractConfig,
    entity_id: str,
    entity_typ: Entities,
    attributes: Optional[dict],
    **kwargs,
):
    """Control an entity via POST http requests."""
    u = Util()
    url: str = await u.entity_url(entity_typ, entity_id)
    additional_data: dict = kwargs.get("additional_data", {})
    token: str = config.token
    websession: ClientSession = config.websession

    headers = DEFAULT_HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"

    if attributes == None and additional_data == {}:
        raise EntityAttributeError(
            "Missing attributes and additional data! At least one must be set"
        )

    body = {}
    body["data"] = additional_data
    body["data"]["type"] = entity_typ.value
    body["data"]["attributes"] = attributes

    resp = await websession.patch(url, data=body, headers=headers)
    json = await resp.json()
    if resp.status != 200:
        raise APIError(
            f"Error code {resp.status} returned from API. Check the provided token!",
            await json,
        )

    if json:
        return json
    else:
        raise Unreachable()


class AbstractEntity(ABC):
    """Superclass of all Entity classes.

    Can also be used to add a custom entity type not implemented in the library with relative ease.
    """

    def __init__(
        self, config: AbstractConfig, entity_typ: Entities, **kwargs: Optional[str]
    ):
        """Prepare some variables and get boilerplate out of the way."""
        self.config: AbstractConfig = config
        self.entity_typ: Entities = entity_typ
        self.name: Optional[str] = kwargs.get("name")
        self.entity_id: Optional[str] = kwargs.get("entity_id")
        self.update: bool = False

        if self.name and self.entity_id == None:
            raise EntityError("Either `name` or `entity_id` must be set")

        self.entity: dict = asyncio.run(self.__setup())
        # Create a shorthand for attributes
        self.attributes = self.entity["attributes"]

        asyncio.create_task(self.__update_entity())
        # TODO: refactor to get entity info only once

    async def __setup(self) -> dict:
        logging.debug(f"Setting up new {self.entity_typ.value}")
        # Get id if it isn't provided, but name is
        if self.entity_id == None:
            logging.warn("entity_id does not exist, retrieving it from API")
            self.entity_id = await id_from_name(
                self.config.websession,
                self.config.token,
                self.entity_typ,
                self.name,  # type: ignore
            )
        else:
            raise Unreachable()

        entity = await get(
            self.config.websession, self.config.token, self.entity_typ, self.entity_id
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

    async def __update_entity(self):
        """Update entity every 5 minutes in background."""
        # TODO: implement proper error handling to update entity if something goes wrong
        while True:
            await asyncio.sleep(300)
            # Ignore type check due to checks already being made in the code itself
            self.entity = await get(self.config.websession, self.config.token, self.entity_typ, self.entity_id)  # type: ignore


class User(AbstractEntity):
    """Entity Class for the users entity type."""

    def __init__(self, config: AbstractConfig, **kwargs: Optional[str]):
        super().__init__(config, Entities.USER, **kwargs)

    async def default_temperature_preference(
        self, temp: Optional[int]
    ) -> Optional[int]:
        """Temperature entities should default to."""
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
            self.config,
            self.entity_id,  # type: ignore
            self.entity_typ,
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
        """Get the temperature scale."""
        scale = True if self.attributes["temperature-scale"] == "C" else False
        return scale

    async def home(self, is_home: bool) -> bool:
        """Check if the structure owner is home."""
        # Once again, type checks have been done in the code
        await control(
            self.config,
            self.entity_id,  # type: ignore
            self.entity_typ,
            {"home": is_home},
        )
        is_home = self.attributes["home"]
        return is_home

    async def structure_heat_cool_mode(self) -> str:
        """Whether or not to cool or heat the structure."""
        heat_cool_mode = self.attributes["structure-heat-cool-mode"]
        return heat_cool_mode

    async def mode_toggle(self) -> str:
        """Toggle the mode for temperature management."""
        mode = self.attributes["mode"]
        mode = "manual" if mode == "auto" else "auto"
        return mode

    async def list_rooms(self) -> list[str]:
        """List the rooms in a structure."""
        # TODO: implement `get_rel`, which gets the relationship link for an entity
        raise NotImplementedError


class Room(AbstractEntity):
    """Entity class for the rooms entity type.

    Similarly to structures, it contains settings pertinent to most users, but
    on a room-by-room basis.
    """

    def __init__(self, config: AbstractConfig, **kwargs: Optional[str]):
        super().__init__(config, Entities.ROOM, **kwargs)

    async def set_point_c(self, temp: Optional[int]) -> int:
        """Set the desired temperature for a room."""
        if temp:
            await control(
                self.config,
                self.entity_id,  # type: ignore
                self.entity_typ,
                {"set-point-c": temp},
            )
        return self.attributes["set-point-c"]

    async def active(self, toggle: bool) -> bool:
        """Get, or toggle wether a room is active."""
        active = self.attributes["active"]
        if toggle == True:
            active = False if active == True else True
            await control(
                self.config,
                self.entity_id,  # type: ignore
                self.entity_typ,
                {"active": active},
            )

        return active

    async def current_temperature_c(self) -> float:
        """Get current temperature in degrees Celsius."""
        cur_temp = self.attributes["current-temperature-c"]
        return cur_temp

    async def current_humidity(self) -> int:
        """Get current humidity in percentage."""
        cur_humid = self.attributes["current-humidity"]
        return cur_humid


# class Puck(AbstractEntity):
#     """Entity class for the pucks entity type.

#     This puck is read-only, and only used for displaying statistics.
#     """

#     async def created_at(self) -> datetime.datetime:
#         raise NotImplementedError

#     # async def


class Vent(AbstractEntity):
    """Entity class for the vents entity type, most likely the most used."""

    def __init__(self, config: AbstractConfig, **kwargs: Optional[str]):
        super().__init__(config, Entities.VENT, **kwargs)

    async def toggle(self):
        """Toggle the vent.

        As of now, vents cannot be anything in between fully open or closed.
        """

    async def open(self) -> int:
        """Open the vent."""
        await control(
            self.config,
            self.entity_id,  # type: ignore
            self.entity_typ,
            {"percent-open": 100},
        )
        self.attributes["percent-open"] = 100

        return 100

    async def close(self) -> int:
        """Close the vent."""
        await control(
            self.config,
            self.entity_id,  # type: ignore
            self.entity_typ,
            {"percent-open": 0},
        )
        self.attributes["percent-open"] = 0

        return 0

    async def status(self) -> int:
        """Check whether or not the vent is open.

        0 is closed and 100 is open.
        """
        return self.attributes["percent-open"]

    async def current_reading(self) -> dict:
        """Get current reading from vent.

        This is technically from another endpoint in the endpoint, but I still
        count them as the same entity, for convenience's sake.
        """
        url = await Util().entity_url(
            self.entity_typ, self.entity_id, current_reading=True
        )
        headers = DEFAULT_HEADERS.copy()
        headers["Authorization"] = f"Bearer {self.config.token}"

        current_reading = self.attributes.get("current_reading")
        if current_reading:
            return current_reading
        else:
            resp = await self.config.websession.get(url, headers=headers)
            json = await resp.json()
            if resp != 200:
                raise APIError(f"Error code {resp.status} returned from API", json)

            if json:
                # TODO: check if this is actually the path for current reading
                current_reading = json["data"]["attributes"]
                return current_reading
            else:
                raise Unreachable
