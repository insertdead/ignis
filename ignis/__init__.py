"""A library for interacting with objects in the Flair API."""
__version__ = "0.1.0"

from ignis.entities import Minisplit, Puck, Room, Structure, Thermostat, User, Vent
from ignis.ignis import Config

__all__ = ["Config", "Structure", "Room", "Vent"]
