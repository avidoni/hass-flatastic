import logging
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from datetime import datetime
import asyncio

_LOGGER = logging.getLogger(__name__)

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


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    api_key = config.get("api_key")
    session = async_get_clientsession(hass)

    # Fetch initial data for flatmates
    data_fetcher = FlatasticDataFetcher(api_key, session)
    await data_fetcher.update_all()

    sensors = []

    # Per-user sensors
    for user in data_fetcher.users:
        sensors.append(FlatasticUserSensor(user, data_fetcher))

    # Additional global sensors
    sensors.extend([
        FlatasticGenericSensor("High Scores", lambda: data_fetcher.get_high_scores()),
        FlatasticGenericSensor("Recent Tasks", lambda: data_fetcher.get_recent_tasks()),
        FlatasticGenericSensor("To-do List", lambda: data_fetcher.get_todo_list()),
        FlatasticGenericSensor("Recent Cashflow", lambda: data_fetcher.get_recent_cashflow()),
    ])

    async_add_entities(sensors, True)


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

    def get_user_by_id(self, user_id):
        return next((u for u in self.users if u["id"] == str(user_id)), None)

    def get_high_scores(self):
        return sorted(
            [(u["firstName"], int(u.get("chorePoints", 0))) for u in self.users],
            key=lambda x: x[1], reverse=True
        )

    def get_recent_tasks(self, count=5):
        tasks = sorted(self.tasks, key=lambda x: x.get("lastDoneDate", 0), reverse=True)
        return [t["title"] for t in tasks[:count] if "title" in t]

    def get_todo_list(self):
        return [t["title"] for t in self.tasks if "currentUser" in t]

    def get_recent_cashflow(self, count=5):
        flows = sorted(self.cashflow, key=lambda x: x.get("date", 0), reverse=True)
        result = []
        for flow in flows[:count]:
            payer = self.get_user_by_id(flow["paidBy"])
            payer_name = payer["firstName"] if payer else "Unknown"
            result.append(f"{payer_name} paid {flow['name']}: {flow['totalSum']} CHF")
        return result


class FlatasticUserSensor(Entity):
    def __init__(self, user_data, data_fetcher):
        self._user = user_data
        self._name = f"Flatastic User {self._user['firstName']}"
        self._state = None
        self._attributes = {}
        self._data_fetcher = data_fetcher

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return f"flatastic_user_{self._user['id']}"

    @property
    def state(self):
        return f"{self._user['firstName']}'s Status"

    @property
    def extra_state_attributes(self):
        user_id = str(self._user["id"])

        # Tasks assigned to this user
        tasks = [t for t in self._data_fetcher.tasks if str(t.get("currentUser")) == user_id]
        task_titles = [t["title"] for t in tasks]

        # User's cashflow
        user_flows = [
            f for f in self._data_fetcher.cashflow
            if str(self._user["id"]) in [str(uid) for uid in f.get("involvedUsers", [])]
        ]
        recent_flows = sorted(user_flows, key=lambda f: f.get("date", 0), reverse=True)[:3]
        flow_info = [f"{f['name']}: {f['totalSum']} CHF" for f in recent_flows]

        # User's balance
        balance_entry = next((s for s in self._data_fetcher.statistics if str(s["id"]) == user_id), {})
        balance = balance_entry.get("balance", 0.0)

        return {
            "email": self._user.get("email"),
            "chorePoints": self._user.get("chorePoints", 0),
            "balance": f"{balance:.2f} CHF",
            "assignedTasks": task_titles,
            "recentCashflow": flow_info,
        }

    async def async_update(self):
        await self._data_fetcher.update_all()


class FlatasticGenericSensor(Entity):
    def __init__(self, name, data_getter):
        self._name = f"Flatastic {name}"
        self._getter = data_getter
        self._state = None
        self._attributes = {}

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return f"flatastic_generic_{self._name.lower().replace(' ', '_')}"

    @property
    def state(self):
        return self._state or "ok"

    @property
    def extra_state_attributes(self):
        return self._attributes

    async def async_update(self):
        try:
            data = self._getter()
            self._state = str(len(data)) if isinstance(data, list) else "ok"
            self._attributes = {"items": data}
        except Exception as e:
            _LOGGER.error("Flatastic sensor update error for %s: %s", self._name, e)
            self._state = "error"
            self._attributes = {}
