"""Manage puck entities"""
# TODO: use classes as data storage? may fix potential issues if subclasses all use one instance of superclass
from ignis.entities.common import Entity, EntityStore
from dataclasses import dataclass

class Puck(Entity):
    """Entity for all flair pucks"""
    def __init__(self, token):
        entity_type = "pucks"
        super().__init__(token, entity_type)

    async def get_status(self, **kwargs):
       """Retrieve information about pucks in the API"""
       entity_id = kwargs.get("entity_id")
       if entity_id is None:
           name = kwargs.get("name")
           entity_id = await super().id_from_name(name)
       return await super().get(entity_id)

@dataclass
class PuckStore(EntityStore):
    """Store all puck entities"""
    name: str
    display_color: str
    is_gateway: bool
    temperature_c: float
