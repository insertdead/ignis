"""Manage thermostats"""
from dataclasses import dataclass

from .common import Entity, EntityStore


class Thermostats(Entity):
    """Entity for all flair thermostats"""

    def __init__(self, token):
        entity_type = "thermostats"
        self.thermostats: list[ThermostatStore] = []
        super().__init__(token, entity_type)

    async def get_status(self, **kwargs):
        """Retrieve information about thermostats in the API"""
        entity_id = kwargs.get("entity_id")
        if entity_id is None:
            name = kwargs.get("name")
            entity_id = await super().id_from_name(name)
        return await super().get(entity_id)

    @Entity.update_entity
    async def update_thermostats(self, entity):
        for key, value in entity:
            entity_attributes = entity[key]["attributes"]
            self.thermostats.append(
                ThermostatStore(
                    entity_attributes["name"],
                    entity["id"],
                    entity_attributes["static-vents"]
                )
            )


@dataclass
class ThermostatStore(EntityStore):
    """Store thermostat entities"""

    name: str
    static_vents: int
