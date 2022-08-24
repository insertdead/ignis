import asyncio
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import TYPE_CHECKING
from urllib.parse import urljoin

from aiohttp import ClientSession, ClientResponse
from typing import Optional, List, Any, Type
from .errors import *


if TYPE_CHECKING:
    from typing import Literal

    _AuthTypes = Literal[
        "Authentication",
        "Authorization",
        "Legacy",
    ]

    _ResourceType = Literal[
        "users",
        "structures",
        "rooms",
        "pucks",
        "thermostats",
        "vents",
        "hvac-units",
    ]


async def to_rel(client: "Client", rel: dict[str, Any]) -> "Relationship":

    typ = next(iter(rel))
    data = rel.get(typ, {})

    return Relationship(client, typ, data)


async def to_rels(client: "Client", rel_dict: dict[str, Any]) -> List["Relationship"]:
    """Shortcut to get a list of relationships from a relationship collection."""
    coros = []
    for rel in rel_dict.values():
        coros.append(to_rel(client, rel))

    rels: List[Relationship] = list(await asyncio.gather(*coros))

    return rels


async def handle_status(res: ClientResponse) -> None:
    status = res.status
    if status > 399:
        if status >= 500:
            raise InternalServerError(await res.text())
        elif status >= 400:
            err = await res.text()
            if status == 400:
                raise InvalidScopeError()
            if status == 403:
                raise InvalidAuthError(f"403 Forbidden:\n {err}")
            if status == 404:
                raise NotFoundError()
            if status == 409:
                raise ApiConflictError()
        else:
            raise MiscApiError(await res.json())


@dataclass
class ApiCredentials:
    token: str
    issued: datetime
    expires_in: int
    auth_typ: "_AuthTypes"

    @classmethod
    async def with_authentication(cls, websession: ClientSession, client_id: str, client_secret: str, legacy_oauth: bool, host: str) -> "ApiCredentials":
        url = f"{host}/oauth2/token" if not legacy_oauth else f"{host}/oauth/token"

        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials"
        }

        async with websession.post(
            url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        ) as res:
            # TODO: handle_status(res: ClientSession) coro
            # handle_status(res)
            json = await res.json()
            
            credentials = ApiCredentials(
                "Authentication",
                datetime.now(),
                json.get("access_token", ""),
                json.get("expires_in", 0),
            )

        return credentials

    @property
    def is_expired(self) -> bool:
        if (self.issued + timedelta(seconds=self.expires_in)) <= datetime.now():
            return True
        else:
            return False


# TODO: relationship stuff may not be completely functional yet
class Relationship:
    def __init__(
        self,
        client: "Client",
        typ: str,
        data: dict[str, Any],
    ) -> None:
        self.client = client
        self.typ = typ
        self.self_link = data.get("links", {}).get("self", "")
        self.related_link = data.get("links", {}).get("related", "")
        self.data = data.get("data", [])

    async def get(self) -> dict[str, Any]:
        return await self.client.get_url(self.self_link)

    async def add(self, res: "Resource" | List["Resource"]) -> None:
        res = res if isinstance(res, list) else [res]
        rel_data = [rel.relationship for rel in res]
        self.data.append(rel_data)
        await self.client.post_url(self.self_link, {"data": rel_data})

    async def update(self, res: "Resource" | List["Resource"]) -> None:
        res = res if isinstance(res, list) else [res]
        rel_data = [rel.relationship for rel in res]
        self.data.append(rel_data)
        await self.client.patch_url(self.self_link, {"data": rel_data})

    async def delete(self, res: "Resource") -> None:
        rel_data = res.relationship
        self.data.remove(rel_data)
        await self.client.delete_url(self.self_link, {"data": rel_data})

    # async def _async_getitem(self, fut: asyncio.Future, key: "_ResourceType") -> None:
        # try:
        #     fut.set_result(await self.client.get(key))
        # except Exception as e:
        #     fut.set_exception(e)


    # def __getitem__(self, key: "_ResourceType") -> asyncio.Future[List["Resource"]]:
    #     loop = asyncio.get_running_loop()
    #     fut = loop.create_future()
    #     loop.create_task(self._async_getitem(fut, key))
    #     return fut


class Resource:
    def __init__(
        self,
        client: "Client",
        id: str,
        typ: "_ResourceType",
        attrs: dict[str, Any],
        rels: List[Relationship]
    ) -> None:
        self.typ: "_ResourceType" = typ
        self.id = id
        self.client = client
        self.attrs = attrs
        self.rels = rels
        self.deleted: bool = False

    @property
    def relationship(self) -> dict[str, str]:
        return {"type": self.typ, "id": self.id}

    async def get(self) -> None:
        new_res = (await self.client.get(self.typ, self.id))[0]

        self.attrs = new_res.attrs
        self.rels = new_res.rels
        self.deleted = new_res.deleted

    async def update(self, attrs: dict[str, Any]) -> None:
        self.attrs = attrs
        await self.client.update(self.typ, self.id, attrs)

    async def delete(self) -> None:
        await self.client.delete(self.typ, self.id)

    async def add_rel(self, rel: Relationship) -> None:
        raise NotImplementedError

    async def del_rel(self, rel: Relationship) -> None:
        raise NotImplementedError


class Client:

    def __init__(
        self,
        websession: ClientSession,
        credentials: ApiCredentials,
        mapper: dict[str, Type[Resource]] = {},
        host = "https://api.flair.co",
    ):
        self.websession = websession
        self.credentials = credentials
        self.mapper = mapper
        self.host = host

        if not asyncio._get_running_loop():
            raise RuntimeError("Clients can only be created within a running event loop!")

    @classmethod
    async def new(cls, client_id: str, client_secret: str, legacy_oauth: bool, mapper: dict[str, Type[Resource]], host: str = "https://api.flair.co") -> "Client":
        websession = ClientSession()
        credentials = await ApiCredentials.with_authentication(websession, client_id, client_secret, legacy_oauth, host)

        return cls(websession, credentials, mapper, host)

    @property
    def token_header(self) -> dict[str, Any]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.credentials.token}"
        }

    def create_url(self, path) -> str:
        return urljoin(self.host, path)

    def resource_url(self, typ: "_ResourceType", id: Optional[str] = None) -> str:
        path = f"{typ}/{id}" if id else f"{typ}"
        return self.create_url(path)

    async def _create_resource(self, typ: "_ResourceType", id: str, attrs: dict[str, Any], rels: List[Relationship]) -> Resource:
        resource = self.mapper.get(typ, Resource)

        return resource(self, id, typ, attrs, rels)

    async def refresh_token(self) -> None:
        if self.credentials.is_expired:
            raise NotImplementedError
        else:
            return

    async def handle_res(self, res: ClientResponse, expect_collection: bool) -> List["Resource"]:
        json: dict[str, Any] = await res.json()

        if not expect_collection:
            data = json.get("data", {})
            typ: "_ResourceType" = data.get("type", "")
            id = data.get("id", "")
            attrs = data.get("attributes", {})
            rels = await to_rels(self, data.get("relationships", {}))

            return [Resource(self, id, typ, attrs, rels)]
            
        else:
            data = json.get("data", [{}])
            resources: List["Resource"] = []

            for resource in data:
                # NOTE: possible to `gather` resources with a `from_identifier` classmethod
                resources.append(await self._create_resource(
                    resource.get("id", ""),
                    resource.get("type", ""),
                    resource.get("attributes", {}),
                    await to_rels(self, resource.get("relationships", {})),
                ))

            return resources

    async def create(self, typ: "_ResourceType", attrs: dict[str, Any] = {}) -> Resource:
        await self.refresh_token()
        url = self.resource_url(typ)

        async with self.websession.post(url, headers=self.token_header, json={"data": {"attributes": attrs}}) as res:
            resource = await self.handle_res(res, False)

        return resource[0]

    async def delete(self, typ: "_ResourceType", id: str) -> None:
        await self.refresh_token()
        url = self.resource_url(typ, id)

        async with self.websession.delete(url, headers=self.token_header) as res:
            await handle_status(res)

    async def get(self, typ: "_ResourceType", id: Optional[str] = None) -> List[Resource]:
        await self.refresh_token()
        url = self.resource_url(typ, id)

        async with self.websession.get(url, headers=self.token_header) as res:
            resources = await self.handle_res(res, False if id else True)

        return resources

    async def get_url(self, url: str, headers: dict[str, str] = {}) -> dict[str, Any]:
        await self.refresh_token()
        headers = {
            **self.token_header,
            **headers,
        }

        async with self.websession.get(url, headers=headers) as res:
            return await res.json()

    async def post_url(self, url: str, json: dict[str, Any], headers: dict[str, str] = {}) -> dict[str, Any]:
        await self.refresh_token()
        headers = {
            **self.token_header,
            **headers,
        }

        async with self.websession.post(url, headers=headers, json=json) as res:
            return await res.json()

    async def patch_url(self, url: str, json: dict[str, Any], headers: dict[str, str] = {}) -> dict[str, Any]:
        await self.refresh_token()
        headers = {
            **self.token_header,
            **headers,
        }

        async with self.websession.patch(url, headers=headers, json=json) as res:
            return await res.json()

    async def delete_url(self, url: str, json: dict[str, Any], headers: dict[str, str] = {}) -> dict[str, Any]:
        await self.refresh_token()
        headers = {
            **self.token_header,
            **headers,
        }

        async with self.websession.delete(url, headers=headers, json=json) as res:
            return await res.json()

    async def update(self, typ: "_ResourceType", id: str, attrs: dict[str, Any]) -> Resource:
        await self.refresh_token()
        url = self.resource_url(typ, id)

        async with self.websession.patch(url, headers=self.token_header, json={"data": {"attributes": attrs}}) as res:
            resource = await self.handle_res(res, False)

        return resource[0]

    async def add_rel(self, res: List[Resource], rel: Relationship) -> None:
        return await rel.add(res)

    async def del_rel(self, res: Resource, rel: Relationship) -> None:
        return await rel.delete(res)
