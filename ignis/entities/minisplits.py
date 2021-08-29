"""Manage minisplit/HVAC entities"""
from dataclasses import dataclass

from .common import Entity, EntityStore


class Minisplits(Entity):
    """Entity for all minisplit/HVAC units"""

    def __init__(self, token):
        entity_type = "hvac-units"
        self.minisplits: list[HvacStore] = []
        super().__init__(token, entity_type)

    async def get_status(self, **kwargs):
        """Retrieve information about minisplits in the API"""
        entity_id = kwargs.get("entity_id")
        if entity_id is None:
            name = kwargs.get("name")
            entity_id = await super().id_from_name(name)
        return await super().get(entity_id)

    @Entity.update_entity
    async def update_minisplits(self, entity):
        for key, value in entity:
            entity_attributes = entity[key]["attributes"]
            self.minisplits.append(
                HvacStore(
                    entity_attributes["name"],
                    entity["id"],
                    entity_attributes["display-color"],
                    entity_attributes["is-gateway"],
                    entity_attributes["temperature-c"],
                )
            )


@dataclass
class HvacStore(EntityStore):
    """Store minisplit/HVAC entities"""

    name: str
    display_color: str
    is_gateway: bool
    temperature_c: float
