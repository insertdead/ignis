"""Test the various entity types from ignis."""
from typing import Coroutine
from ignis import utils
import pytest
import asyncio
from ignis.utils import APIError, Entities


async def test_entity_types(websession, credentials):
    assert len(Entities) == 7, "Incorrect number of entities"


async def test_entities_exist_in_api(websession, config):
    entities: list[Coroutine] = []
    for entity in Entities:
        entities.append(utils.get_list(websession, config.token, entity))

    try:
        asyncio.gather(*entities)

    except APIError:
        pytest.fail("API Error received! Entity in `Entities` enum most likely does not exist in API")


class TestVents:
    """Test capabilites of vents"""


class TestStructures:
    """Test capabilities of structures"""
