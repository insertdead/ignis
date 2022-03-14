"""Test the various entity types from ignis."""
from ignis import entities
from ignis.utils import Entities

def test_entity_types():
    assert len(Entities) == 7, "Incorrect number of entities"
    for _ in Entities:
        assert True

class TestVents:
    """Test capabilites of vents"""

class TestStructures:
    """Test capabilities of structures"""
