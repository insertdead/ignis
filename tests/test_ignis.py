# TODO: Update to work with refactor
import os

import pytest
from aiohttp import ClientSession

from ignis import __version__
from ignis.entities import common

CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")


@pytest.fixture
async def get_token():
    assert CLIENT_ID is not None, "$CLIENT_ID variable unset"
    assert CLIENT_SECRET is not None, "$CLIENT_ID variable unset"

    a = common.Auth(CLIENT_ID, CLIENT_SECRET)
    return await a.oauth_token()


def test_version():
    assert __version__ == "0.1.0"


@pytest.mark.asyncio
async def api_works():
    url = await common.Util().create_url("/api/")
    headers = common.HEADERS
    async with ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                pytest.fail(f"status code {resp.status} received from API")


@pytest.mark.asyncio
async def test_auth(get_token):
    print(get_token)
