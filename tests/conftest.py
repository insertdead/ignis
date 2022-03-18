import asyncio
import pytest
import pytest_asyncio
import os
from typing import AsyncGenerator, AsyncIterable
from aiohttp import ClientSession
from ignis import BasicConfig
from ignis.ignis import SCOPE


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close


@pytest.fixture(scope="package")
def credentials():
    return {
        "client_id": os.environ.get("CLIENT_ID"),
        "client_secret": os.environ.get("CLIENT_SECRET"),
    }


@pytest.fixture(scope="package")
def legacy_credentials():
    return {
        "client_id": os.environ.get("LEGACY_CLIENT_ID"),
        "client_secret": os.environ.get("LEGACY_CLIENT_SECRET"),
    }


@pytest_asyncio.fixture(scope="package")
async def websession() -> AsyncGenerator[ClientSession, ClientSession] | AsyncIterable[ClientSession]:
    websession = ClientSession()
    yield websession
    await websession.close()


@pytest_asyncio.fixture(scope="package", autouse=True)
async def config(credentials) -> AsyncGenerator[BasicConfig, BasicConfig] | AsyncIterable[BasicConfig]:
    config = await BasicConfig.create_config(credentials["client_id"], credentials["client_secret"], SCOPE, "DEBUG")
    yield config
    await config.close()


@pytest_asyncio.fixture(scope="package")
async def legacy_config(legacy_credentials) -> AsyncGenerator[BasicConfig, BasicConfig] | AsyncIterable[BasicConfig]:
    legacy_config = await BasicConfig.create_config(
        legacy_credentials["client_id"],
        legacy_credentials["client_secret"],
        SCOPE,
        "DEBUG",
        legacy_oauth=True
    )
    yield legacy_config
    await legacy_config.close()
