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

    async def control(self, **kwargs):
        """Change settings of structures"""
        # NOTE: not sure if possible to control structure settings or not; check later
        entity_id = kwargs.get("entity_id")
        temperature_scale = kwargs.get("temperature_scale")
        is_home = kwargs.get("is_home")
        structure_heat_cool_mode = kwargs.get("structure_heat_cool_mode")
        auto_mode = kwargs.get("auto_mode")
        body = {
            "temperature_scale": temperature_scale,
            "home": is_home,
            "structure_heat_cool_mode": structure_heat_cool_mode,
            "auto_mode": auto_mode,
        }
        if entity_id is None:
            name = kwargs.get("name")
            entity_id = await super().id_from_name(name)
        return await super().control(entity_id, body)

    @Entity.update_entity
    async def update_structures(self, entity):
        for key, value in entity:
            entity_attributes = entity[key]["attributes"]
            self.structures.append(
                StructureStore(
                    entity_attributes["name"],
                    entity["id"],
                    entity_attributes["temperature_scale"],
                    entity_attributes["home"],
                    entity_attributes["structure-heat-cool-mode"],
                    entity_attributes["mode"]
                )
            )


@dataclass
class StructureStore(EntityStore):
    """Store structure entities"""

    name: str
    temperature_scale: "C" | "F"
    home: bool
    structure_heat_cool_mode: str
    mode: str
