"""Manage vent entities"""
from ignis.entities.common import Entity, EntityStore
from dataclasses import dataclass


class Vent(Entity):
    """Entity for all flair vents"""
    def __init__(self, token):
        entity_type = "vents"
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

@dataclass
class VentStore(EntityStore):
    """Store all vents entities"""
    name: str
    is_open: bool # or int? not sure if I should stray from using bools in favor of a miniscule performance increase
    reason: str
