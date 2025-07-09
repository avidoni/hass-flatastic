# flatastic_api.py

import logging
from datetime import datetime

BASE_URL = "https://api.flatastic-app.com/index.php/api"
HEADERS = {
    "accept": "application/json, text/plain, */*",
    "x-api-version": "2.0.0",
    "x-client-version": "2.3.20",
}

API_ENDPOINTS = {
    "shopping_list": "/shoppinglist",
    "task_list": "/chores",
    "wg_info": "/wg",
    "cashflow": "/cashflow",
    "cashflow_statistics": "/cashflow/statistics",
}

_LOGGER = logging.getLogger(__name__)


class FlatasticDataFetcher:
    def __init__(self, api_key, session):
        self.api_key = api_key
        self.session = session
        self.headers = HEADERS.copy()
        self.headers["x-api-key"] = api_key

        self.users = []
        self.tasks = []
        self.cashflow = []
        self.statistics = []
        self.shopping = []

    async def _fetch(self, endpoint_key):
        url = BASE_URL + API_ENDPOINTS[endpoint_key]
        try:
            async with self.session.get(url, headers=self.headers) as response:
                return await response.json()
        except Exception as e:
            _LOGGER.error("Flatastic API fetch error: %s", e)
            return []

    async def update_all(self):
        wg_info = await self._fetch("wg_info")
        self.users = wg_info.get("flatmates", [])
        self.tasks = await self._fetch("task_list")
        self.cashflow = await self._fetch("cashflow")
        self.statistics = await self._fetch("cashflow_statistics")
        self.shopping = await self._fetch("shopping_list")
        
    @property
    def currency(self):
        return self.wg_info.get("currency", "€")
    
    async def add_shopping_item(self, item_data):
        url = BASE_URL + API_ENDPOINTS["shopping_list"]
        try:
            async with self.session.post(url, headers=self.headers, json=item_data) as resp:
                if resp.status in (200, 201):
                    return await resp.json()
                else:
                    text = await resp.text()
                    _LOGGER.error("Failed to add shopping item: %s, response: %s", resp.status, text)
        except Exception as e:
            _LOGGER.error("Error adding shopping item: %s", e)
        return None


    async def delete_shopping_item(self, item_id):
        url = f"{BASE_URL}/shoppinglist/item/{item_id}"
        try:
            async with self.session.delete(url, headers=self.headers) as resp:
                if resp.status not in (200, 204):
                    _LOGGER.error("Failed to delete shopping item ID %s: %s", item_id, resp.status)
        except Exception as e:
            _LOGGER.error("Error deleting shopping item ID %s: %s", item_id, e)

        
    async def toggle_shopping_item(self, item_id):
        url = f"{BASE_URL}/shoppinglist/toggle_item?item_id={item_id}"
        try:
            async with self.session.get(url, headers=self.headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    _LOGGER.error("Failed to toggle shopping item ID %s: %s", item_id, resp.status)
        except Exception as e:
            _LOGGER.error("Error toggling shopping item ID %s: %s", item_id, e)
        return None

    def get_user_by_id(self, user_id):
        return next((u for u in self.users if u["id"] == str(user_id)), None)

    def get_high_scores(self):
        return sorted(
            [(u["firstName"], int(u.get("chorePoints", 0))) for u in self.users],
            key=lambda x: x[1], reverse=True
        )

    def get_cashflow_statistics(self):
        stats = {}
        for entry in self.statistics:
            user_id = str(entry["id"])
            user = self.get_user_by_id(user_id)
            if user:
                stats[user["firstName"]] = {
                    "balance": entry.get("balance", 0.00),
                }
        return stats

    def get_recent_tasks(self, count=5):
        tasks = sorted(self.tasks, key=lambda x: x.get("lastDoneDate", 0), reverse=True)
        return [t["title"] for t in tasks[:count] if "title" in t]

    def get_recent_cashflow(self, count=5):
        currency = self.currency
        flows = sorted(self.cashflow, key=lambda x: x.get("date", 0), reverse=True)
        result = []
        for flow in flows[:count]:
            payer = self.get_user_by_id(flow["paidBy"])
            payer_name = payer["firstName"] if payer else "Unknown"
            result.append(f"{payer_name} paid {flow['name']}: {flow['totalSum']} {currency}")
        return result
    
    def get_shopping_list(self, include_data=False):
        if include_data:
            return self.shopping
        return [item["itemName"] for item in self.shopping if "itemName" in item]
