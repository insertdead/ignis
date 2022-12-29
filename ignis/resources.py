"""Resource classes & mapper for easy use"""
from enum import Enum

from .ignis import Resource, Client, Relationship
from typing import TYPE_CHECKING, List, Any

if TYPE_CHECKING:
    from .ignis import _ResourceType


class Room(Resource):
    def get_temp(self) -> float:
        return self.attrs.get("set-point-c", -1.0)

    async def set_temp(self, temp_c: float) -> None:
        await self.update({"set-point-c": temp_c})

    # async def get_resource(self, typ: "_ResourceType") -> List[Resource]:
    #     return NotImplemented


class HvacUnit(Resource):
    _hass_hvac_to_flair_modes = {
        "auto": "Auto",
        "cool": "Cool",
        "heat": "Heat",
        "fan_only": "Fan",
    }

    _hass_modes_to_flair_pwr = {
        "off": "Off",
    }

    async def set_hvac_mode(self, mode: str) -> None:
        self_mode = self.attrs.get("mode", "Auto")
        self_power = self.attrs.get("power", "Off")

        if self_power == "Off" and mode != "off":
            self_power = "On"

        await self.update(
            {
                "mode": self._hass_hvac_to_flair_modes.get(mode, self_mode),
                "power": self._hass_modes_to_flair_pwr.get(mode, self_power),
            }
        )

    async def get_hvac_mode(self) -> str:
        return self.attrs.get("mode") if self.attrs.get("power") != "Off" else "Off"  # type: ignore

    async def get_temp(self) -> float:
        # FIXME: bug here but im too lazy to fix it rn
        return self.attrs.get("temperature", -1.0)
