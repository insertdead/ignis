import asyncio
import os
from typing import AsyncGenerator, AsyncIterable

import pytest
import pytest_asyncio
from aiohttp import ClientSession

from ignis import BasicConfig, __version__, utils
from ignis.entities import get_list


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close


CREDENTIALS = {
    "client_id": os.environ.get("CLIENT_ID"),
    "client_secret": os.environ.get("CLIENT_SECRET"),
    "legacy": {
        "client_id": os.environ.get("LEGACY_CLIENT_ID"),
        "client_secret": os.environ.get("LEGACY_CLIENT_SECRET"),
    }
}


# TODO: find out how to properly use async generators
@pytest_asyncio.fixture(scope="session")
async def websession() -> AsyncGenerator[ClientSession, ClientSession] | AsyncIterable[ClientSession]:
    websession = ClientSession()
    yield websession
    await websession.close()


@pytest_asyncio.fixture(scope="session")
async def config() -> AsyncGenerator[BasicConfig, BasicConfig] | AsyncIterable[BasicConfig]:
    scope = utils.SCOPE + "+vents.view"
    config = await BasicConfig.create_config(CREDENTIALS["client_id"], CREDENTIALS["client_secret"], scope, "DEBUG")
    yield config
    await config.close()


@pytest_asyncio.fixture(scope="session")
async def legacy_config() -> AsyncGenerator[BasicConfig, BasicConfig] | AsyncIterable[BasicConfig]:
    scope = utils.SCOPE + "+vents.view"
    legacy_config = await BasicConfig.create_config(
        CREDENTIALS["client_id"],
        CREDENTIALS["client_secret"],
        scope,
        "DEBUG",
        legacy_oauth=True
    )
    yield legacy_config
    await legacy_config.close()


def test_version():
    assert __version__ == "0.1.0"


def test_credentials():
    legacy = CREDENTIALS["legacy"]

    assert CREDENTIALS["client_id"], "$CLIENT_ID variable unset"
    assert CREDENTIALS["client_secret"], "$CLIENT_SECRET variable unset"
    assert legacy["client_id"], "$LEGACY_CLIENT_ID variable unset"
    assert legacy["client_secret"], "$LEGACY_CLIENT_SECRET variable unset"


async def test_api_status(websession):
    url = await utils.Util().create_url("/api/")
    headers = utils.DEFAULT_HEADERS
    resp = await websession.get(url, headers=headers)
    assert resp.status == 200, f"status code {resp.status} received from API"


async def test_auth(websession, config):
    vent_list: dict = await get_list(websession, config.token, utils.Entities.VENT)
    assert type(vent_list) == dict, "Vent list returned is not a list!"
