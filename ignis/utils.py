"""Error classes and utilities for Ignis"""
from dataclasses import dataclass
from enum import Enum, unique
from urllib.parse import urljoin
import logging
from typing import Optional
from aiohttp import ClientSession

HOST = "https://api.flair.co"
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


@dataclass
class Scope:
    view: Optional[list[Entities]]
    edit: list[Entities]

    def __post_init__(self):
        """Check for duplicates between edit and view and delete the duplicate in view."""
        index = 0
        if self.view is None:
            self.view = []

        for v in self.view:
            if v in self.edit:
                del self.view[index]
            index += 1

    def to_str(self) -> str:
        """Compile Scope into a string usable by the API"""
        scope = ""

        for v in self.view:  # type: ignore
            scope += f"{v.value}.view+"

        for e in self.edit:
            scope += f"{e.value}.view+{e.value}.edit+"
        scope = scope[:-1]

        return scope


# Exceptions
class EntityError(Exception):
    """General Error class for errors related to the `Entity` class.

    Uses include:
        - Incorrect arguments fed to the `Entity` class
        - Entity name or id does not exist, or do not match

    Should *not* be used without an argument
    """

    def __init__(self, *args):
        self.message = args[0] if args else None

    def __str__(self):
        if self.message:
            return f"EntityError: {self.message}"
        else:
            raise Unreachable


class EntityAttributeError(Exception):
    """Raise when an attribute is wrongly set, or doesn't exist."""

    def __init__(self, *args: str):
        self.message = args[0] if args else None

    def __str__(self) -> str:
        if self.message:
            return f"EntityAttributeError: {self.message}"
        else:
            return "EntityAttributeError: Attribute is incorrect, or doesn't exist"


class APIError(Exception):
    """Raise when API returns an error, and print the error out.

    If a normally unreachable state is reached in a part of code interacting with the API,
    this should be preferred over `Unreachable()`
    """

    def __init__(self, code: str, *args: str):
        self.code = code
        self.error = args[0] if len(args) >= 1 else None
        self.message = args[1] if len(args) >= 2 else None

    def __str__(self) -> str:
        if self.message and self.error:
            return f"{self.message}\nHTTP error received: {self.error}"
        elif self.error:
            return f"Error received from the API ({self.code})\n{self.error}"
        else:
            return "An unknown error occurred with the API. Please create an issue at <https://github.com/insertdead/ignis/issues>" # noqa


class Unreachable(Exception):
    """Used in scenarios when something should be not possible to reach.

    Examples:
        - A control flow statement that should not evaluate to `True`
        - Reaching the end of an action that should have ended earlier or in some other way
    """

    def __init__(self, *args: str):
        self.message = args[0] if args else None

    def __str__(self) -> str:
        if self.message:
            return f"Unreachable: {self.message}"
        else:
            return "Unreachable: This should not be possible"


# Utlilities functions
async def create_url(path: str):
    """Create a valid URL for the API"""
    url = urljoin(HOST, path)
    return url


async def entity_url(typ: Entities, entity_id, current_reading=False):
    """Create a valid URL for an entity in the API"""
    if current_reading:
        url = await create_url(
            f"/api/{typ.value}/{entity_id}/current_reading"
        )
    else:
        url = await create_url(f"/api/{typ.value}/{entity_id}")
    return url


async def get(
    websession: ClientSession, token: str, typ: Entities, id: str
) -> dict:
    """Retrieve an entity from the API.

    This should normally be never used anywhere outside the library, but may be
    used when creating a new entity if needed.
    """
    url: str = await entity_url(typ, id)
    headers = DEFAULT_HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"

    logging.info(
        f'`get()` function called for entity "{id}" of type {typ.value}.'
    )

    resp = await websession.get(url, headers=headers)
    if resp.status != 200:
        raise APIError(f"Error code {resp.status} returned from API", await resp.json())
    json = await resp.json()

    if json:
        return json
    else:
        raise Unreachable()


async def get_list(websession: ClientSession, token: str, typ: Entities) -> dict:
    """Get a list of entities of a certain type."""
    url: str = await create_url(f"/api/{typ.value}")
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
    websession: ClientSession,
    token: str,
    entity_id: str,
    entity_typ: Entities,
    attributes: Optional[dict],
    **kwargs,
):
    """Control an entity via POST http requests."""
    url: str = await entity_url(entity_typ, entity_id)
    additional_data: dict = kwargs.get("additional_data", {})

    headers = DEFAULT_HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"

    if not attributes and not additional_data == {}:
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


class ColourFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    log_format = "%(asctime)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + log_format + reset,
        logging.INFO: grey + log_format + reset,
        logging.WARNING: yellow + log_format + reset,
        logging.ERROR: red + log_format + reset,
        logging.CRITICAL: bold_red + log_format + reset,
    }

    def format(self, record: logging.LogRecord) -> str:
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
