"""Common code between all entities"""
from dataclasses import dataclass, field
from urllib.parse import urljoin
from functools import wraps

from aiohttp import ClientResponse, ClientSession
from async_lru import alru_cache

HOST = "https://api.flair.co"
SCOPE = "thermostats.view+structures.view+structures.edit"


class Util:
    """Common utilities to reduce boiler"""

    async def create_url(self, path):
        """Create a valid URL for the API"""
        url = urljoin(HOST, path)
        return url

    async def entity_url(self, entity_type, entity_id):
        """Create a valid entity URL"""
        url = await self.create_url(f"/api/{entity_type}/{entity_id}")
        return url


class Auth:
    """Authenticate with API"""

    def __init__(self, ident, access_token, scope, logger: logging.getLogger()):
        self.ident = ident
        self.access_token = access_token
        self.scope = scope
        self.logger = logger
        self.opts = {
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/json",
        }

    async def oauth_token(self):
        """Retrieve OAuth2 token from API"""
        u = Util()
        url = await u.create_url("/oauth/token")
        credentials = {
            "client_id": self.ident,
            "client_secret": self.access_token,
            "grant_type": 'client_credentials',
        }

        async with ClientSession() as session:
            async with session.post(url, params=credentials, headers=self.opts) as resp:
                json = await resp.json()
                token = json["access_token"]
                self.logging.info(f"status returned from method {__name__}")
                return token


class Entity:
    """Template for entity types"""

    def __init__(self, token):
        self.entity_type = None
        self.entity_list: list[EntityStore] = []
        self.opts = {
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

    async def get_list(self):
        """Get a list of entities of a certain type"""
        u = Util()
        url = await u.create_url(f"/api/{self.entity_type}")
        async with ClientSession() as session:
            async with session.get(url, headers=self.opts) as resp:
                json = await resp.json()
                self.entity = json
                return await resp.status

    async def get(self, entity_id):
        """Get information on an entity in the API"""
        u = Util()
        url = await u.entity_url(self.entity_type, entity_id)
        async with ClientSession() as session:
            async with session.get(url, headers=self.opts) as resp:
                json = await resp.json()
                self.entity_response = json
                return await resp.status

    # FIXME: Async wrappers are weird
    def update_entity(func): # noqa
        """Wrapper to update list of entities"""
        async def update(self):
            status = await self.get_list()
            await func(self.entity)
            return status

        return update

    async def control(self, entity_id, body):
        """POST request to API to change entity properties"""
        u = Util()
        url = await u.entity_url(self.__name__, entity_id)
        __body = {"data": {"type": self.entity_type, "attributes": body}}
        async with ClientSession() as session:
            async with session.patch(url, data=__body, headers=self.opts) as resp:
                return await resp.status

    @alru_cache
    async def id_from_name(self, name):
        """Get entity ID from its name"""
        await self.get_list()
        entity_num = next(
            (
                i
                for i, item in enumerate(self.entity)
                if item["attributes"]["name"] is name
            ),
            None,
        )
        entity_id = self.entity[entity_num]["id"]
        return entity_id


# TODO: EntityStore dataclass for all entity types
# TODO: have one instance EntityStore contain all entities within their respective stores, or something else?
# FIXME: Rename *Stores to something more appropriate, and by extension the other classes
@dataclass
class EntityStore:
    """Store all entities in a dataclass"""

    name: str
    entity_id: str = field(repr=False)
