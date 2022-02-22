"""A library for interacting with objects in the Flair API."""
__version__ = "0.1.0"

from ignis.entities import Room, Structure, User, Vent
from ignis.ignis import AbstractConfig, BasicConfig

__all__ = ["BasicConfig", "Structure", "Room", "Vent"]
