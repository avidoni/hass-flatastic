# todo.py

import logging
import uuid
from datetime import datetime

from homeassistant.components.todo import TodoListEntity, TodoItem, TodoListEntityFeature
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .flatastic_api import FlatasticDataFetcher
import voluptuous as vol
from homeassistant.components.todo import DOMAIN as TODO_DOMAIN
from homeassistant.const import CONF_API_KEY
import homeassistant.helpers.config_validation as cv


PLATFORM_SCHEMA = vol.Schema({
    vol.Required(CONF_API_KEY): cv.string,
}, extra=vol.ALLOW_EXTRA)

_LOGGER = logging.getLogger(__name__)



async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    api_key = config.get("api_key")
    session = async_get_clientsession(hass)
    fetcher = FlatasticDataFetcher(api_key, session)

    try:
        await fetcher.update_all()
        async_add_entities([FlatasticShoppingListEntity(fetcher)], True)
    except Exception as e:
        _LOGGER.error("Error setting up hass-flatastic todo: %s", e)

class FlatasticShoppingListEntity(TodoListEntity):
    def __init__(self, data_fetcher):
        self._data_fetcher = data_fetcher
        self._attr_name = "Flatastic Shopping List"
        self._attr_unique_id = "flatastic_shopping_list"
        self._attr_has_entity_name = True
        self._attr_supported_features = (
            TodoListEntityFeature.CREATE_TODO_ITEM |
            TodoListEntityFeature.DELETE_TODO_ITEM |
            TodoListEntityFeature.UPDATE_TODO_ITEM
        )
        self._attr_todo_items = []

    @property
    def state(self):
        if self._attr_todo_items is None:
            return "unknown"
        return f"{len(self._attr_todo_items)} items"
    

    async def async_update(self):
        await self._data_fetcher.update_all()
        raw_items = self._data_fetcher.get_shopping_list(include_data=True)

        items = []
        for item in raw_items:
            uid = str(item["id"])
            summary = item.get("itemName", "")
            if not summary:
                _LOGGER.warning("Skipping item with empty summary: %s", item)
                continue
            
            # If bought == 0 => needs_action, else done
            status = "needs_action" if item.get("bought", 1) == 0 else "completed"
            items.append(TodoItem(summary=summary, uid=uid, status=status))

        self._attr_todo_items = items

    async def async_get_todo_items(self) -> list[TodoItem]:
        return self._attr_todo_items or []
    
    async def async_create_todo_item(self, item: TodoItem) -> str:
        new_item = {
            "name": item.summary,  # <-- change here from "itemName" to "name"
            "amount": "1",
            "priority": 3,
            "bought": 0,
            "date": int(datetime.now().timestamp()),
        }


        created = await self._data_fetcher.add_shopping_item(new_item)

        await self.async_update()
        self.async_write_ha_state()

        return str(created.get("id")) if created else str(uuid.uuid4())

    async def async_update_todo_item(self, item: TodoItem):
        result = await self._data_fetcher.toggle_shopping_item(item.uid)
        if result is None:
            _LOGGER.error(f"Failed to toggle shopping item with ID {item.uid}")
            return

        # Refresh data and notify HA about changes
        await self.async_update()
        self.async_write_ha_state()



    async def async_delete_todo_item(self, uid: str):
        await self._data_fetcher.delete_shopping_item(uid)
        await self.async_update()
        self.async_write_ha_state()

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        """Delete todo items by their UID."""
        for uid in uids:
            try:
                await self.async_delete_todo_item(uid)
                _LOGGER.debug("Deleted shopping item with ID %s", uid)
            except Exception as e:
                _LOGGER.error("Failed to delete shopping item ID %s: %s", uid, e)

        # Refresh list
        await self.async_update()
        self.async_write_ha_state()

    