# TODO: Update to work with refactor
import asyncio
import os

import pytest
from aiohttp import ClientSession

from ignis import BasicConfig, Room, Structure, User, Vent, __version__, utils
from ignis.entities import get_list
from ignis.ignis import AbstractConfig

CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")


def test_version():
    assert __version__ == "0.1.0"


@pytest.fixture
async def websession() -> ClientSession:
    return ClientSession()


@pytest.mark.asyncio
async def test_api_status(websession):
    url = await utils.Util().create_url("/api/")
    headers = utils.DEFAULT_HEADERS
    resp = await websession.get(url, headers=headers)
    if resp.status != 200:
        pytest.fail(f"status code {resp.status} received from API")


@pytest.fixture
def config(websession) -> BasicConfig:
    assert CLIENT_ID is not None, "$CLIENT_ID variable unset"
    assert CLIENT_SECRET is not None, "$CLIENT_ID variable unset"

    scope = utils.SCOPE + "+vents.view"
    config = BasicConfig(CLIENT_ID, CLIENT_SECRET, scope, "DEBUG")
    return config


@pytest.mark.asyncio
async def test_auth(websession, config: BasicConfig):
    vent_list: dict = await get_list(websession, config.token, utils.Entities.VENT)
    if type(vent_list) != dict:
        pytest.fail("Vent list returned is not a list!")


# HACK: initialize ClientSession() instances in async __init() coroutines instead of elsewhere.
#   This would help avoid running into issues with the event loop that asyncio starts itself.
# implement proper way to run async init method and block until done - not sure if this is even possible
#   Most likely going to have to resort to only creating instances within an async context manager. Could also be made a function in the library
# Example:
#   async def createConfig() -> AbstractConfig:
#       assert CLIENT_ID is not None, "$CLIENT_ID variable unset"
#       assert CLIENT_SECRET is not None, "$CLIENT_ID variable unset"
#       scope = utils.SCOPE + "+vents.view"
#       async with BasicConfig(await websession(), CLIENT_ID, CLIENT_SECRET, scope, "DEBUG") as config:
#           return config
#
#   conf = asyncio.run(createConfig())
#   print(conf.token)
