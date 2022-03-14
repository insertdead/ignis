"""Error classes and utilities for Ignis"""
from enum import Enum, unique
from urllib.parse import urljoin
import logging

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
        self.error = args[1] if args[1] else None
        self.message = args[2] if args[2] else None

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


# Utlilities packaged into one class
class Util:
    """Common utilities packaged into one class for convenience."""

    async def create_url(self, path: str):
        """Create a valid URL for the API"""
        url = urljoin(HOST, path)
        return url

    async def entity_url(self, entity_typ: Entities, entity_id, current_reading=False):
        """Create a valid URL for an entity in the API"""
        if current_reading:
            url = await self.create_url(
                f"/api/{entity_typ.value}/{entity_id}/current_reading"
            )
        else:
            url = await self.create_url(f"/api/{entity_typ.value}/{entity_id}")
        return url


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
