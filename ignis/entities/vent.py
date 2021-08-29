"""Manage vent entities"""
from dataclasses import dataclass

from .common import Entity, EntityStore


class Vent(Entity):
    """Entity for all flair vents"""

    def __init__(self, token):
        entity_type = "vents"
        self.vents: list[VentStore] = []
        super().__init__(token, entity_type)

    async def control(self, status: bool, **kwargs):
        """Control the vents as if they were a switch"""
        entity_id = kwargs.get("entity_id")
        status = 100 if status is True else 0
        reason = kwargs.get("custom_reason") if not None else "ignis"
        body = {"percent_open": status, "reason": f"{status} by {reason}"}
        if entity_id is None:
            name = kwargs.get("name")
            entity_id = await super().id_from_name(name)
        return await super().control(entity_id, body)

    @Entity.update_entity
    async def update_vents(self, entity):
        # Pretty much just temporary pseudocode
        # Probably gonna have to do some kind of dictionary comprehension
        for key, value in entity:
            entity_attributes = entity[key]["attributes"]
            self.vents.append(
                VentStore(
                    entity_attributes["name"],
                    entity["id"],
                    entity_attributes["percent_open"],
                    entity_attributes["reason"],
                )
            )


@dataclass
class VentStore(EntityStore):
    """Store all vents entities"""

    name: str
    is_open: bool | int  # or keep as int? not sure if I should stray from using bools in favor of a miniscule performance increase
    reason: str

    # FIXME: if self.is_open == None then will be converted to False
    # Maybe this: ``else if not None:``
    def __post_init__(self):
        if self.is_open is 100:
            self.is_open = True
        else:
            self.is_open = False
