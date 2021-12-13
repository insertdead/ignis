"""Error classes and utilities for Ignis"""
from urllib.parse import urljoin

from ignis.ignis import HOST, Entities


# Exceptions
class EntityError(Exception):
    """General Error class for errors related to the `Entity` class
    Uses include:
        - Incorrect arguments fed to the `Entity` class
        - Entity name or id does not exist, or do not match

    Should *not* be used without an argument"""

    def __init__(self, *args):
        self.message = args[0] if args else None

    def __str__(self):
        if self.message:
            return f"EntityError: {self.message}"
        else:
            raise Unreachable


class EntityAttributeError(Exception):
    """Raise when an attribute is wrongly set, or doesn't exist"""

    def __init__(self, *args: str):
        self.message = args[0] if args else None

    def __str__(self) -> str:
        if self.message:
            return f"EntityAttributeError: {self.message}"
        else:
            return "EntityAttributeError: Attribute is incorrect, or doesn't exist"


class Unreachable(Exception):
    """Used in scenarios when something should be not possible to reach
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
    """Common utilities packaged into one class for convenience"""

    async def create_url(self, path: str):
        """Create a valid URL for the API"""
        url = urljoin(HOST, path)
        return url

    async def entity_url(self, entity_type: Entities, entity_id):
        """Create a valid URL for an entity in the API"""
        url = await self.create_url(f"/api/{entity_type.name}/{entity_id}")
        return url