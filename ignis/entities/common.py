"""Common code between all entities"""
from aiohttp import ClientSession, ClientResponse
from urllib.parse import urljoin
from dataclasses import dataclass
from functools import lru_cache

HOST = "https://api.flair.co"


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

    def __init__(self, ident, access_token):
        self.ident = ident
        self.access_token = access_token

    async def oauth_token(self):
        """Retrieve OAuth2 token from API"""
        u = Util()
        url = await u.create_url("/oauth/token")
        credentials = {
            "client_id": self.ident,
            "client_token": self.access_token,
            "grant_type": "credentials",
        }
        async with ClientSession as session:
            async with session.post(url, params=credentials) as resp:
                json = await resp.json()
                self.token = json["access_token"]
                return await resp.status


class Entity:
    """Template for entity types"""

    def __init__(self, token):
        self.token = token
        self.entity_type = None
        self.opts = {
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/json",
        }

    async def get_list(self):
        """Get a list of entities of a certain type"""
        u = Util()
        url = await u.create_url(f"/api/{self.entity_type}")
        async with ClientSession as session:
            async with session.get(url, params=self.opts) as resp:
                self.entity = await resp.json()
                return await resp.status

    async def get(self, entity_id):
        """Get information on an entity in the API"""
        u = Util()
        url = await u.entity_url(self.entity_type, entity_id)
        async with ClientSession as session:
            async with session.get(url, params=self.opts) as resp:
                json = await resp.json()
                self.entity_response = json
                return await resp.status

    async def control(self, entity_id, body):
        """POST request to API to change entity properties"""
        u = Util()
        url = await u.entity_url(self.__name__, entity_id)
        __body = {"data": {"type": self.entity_type, "attributes": body}}
        async with ClientSession as session:
            async with session.patch(url, data=__body, params=self.opts) as resp:
                return await resp.status

    @lru_cache
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
@dataclass
class EntityStore:
    """Store all entities in a dataclass"""
    name: str
    entity_type: str
    entity_id: str

#
# TESTING ONLY; REMOVE WHEN DONE
#
def main():
    obj = EntityStore("vents", "abababababababa", "joe mama")
    print(obj)

if __name__ == '__main__':
    main()
