"""Manage structures"""
from dataclasses import dataclass

from .common import Entity, EntityStore


class Structures(Entity):
    """Entity for all flair structures"""

    def __init__(self, token):
        entity_type = "structures"
        self.structures: list[StructureStore] = []
        super().__init__(token, entity_type)

    async def get_status(self, **kwargs):
        """Retrieve information about structures in the API"""
        entity_id = kwargs.get("entity_id")
        if entity_id is None:
            name = kwargs.get("name")
            entity_id = await super().id_from_name(name)
        return await super().get(entity_id)

    @Entity.update_entity
    async def update_structures(self, entity):
        for key, value in entity:
            entity_attributes = entity[key]["attributes"]
            self.structures.append(
                StructureStore(
                    entity_attributes["name"],
                    entity["id"],
                    entity_attributes["set-point-c"],
                    entity_attributes["current-temperature-c"],
                    entity_attributes["current-humidity"],
                    entity_attributes["active"],
                )
            )


@dataclass
class StructureStore(EntityStore):
    """Store structure entities"""

    name: str
    set_point_c: float
    current_temperature_c: float
    current_humidity: float
    active: bool
