# sensor.py

import logging
from datetime import datetime
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .flatastic_api import FlatasticDataFetcher


_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    api_key = config.get("api_key")
    session = async_get_clientsession(hass)
    data_fetcher = FlatasticDataFetcher(api_key, session)

    await data_fetcher.update_all()

    sensors = []

    for user in data_fetcher.users:
        sensors.append(FlatasticUserSensor(user, data_fetcher))

    for task in data_fetcher.tasks:
        sensors.append(FlatasticTaskSensor(task, data_fetcher))

    sensors.append(FlatasticGenericSensor("Recent Cashflow", lambda: data_fetcher.get_recent_cashflow()))
    # sensors.append(FlatasticGenericSensor("Shopping List", lambda: data_fetcher.get_shopping_list()))
    # sensors.append(FlatasticGenericSensor("Cashflow Statistics", lambda: data_fetcher.get_cashflow_statistics()))

    async_add_entities(sensors, True)


class FlatasticUserSensor(Entity):
    def __init__(self, user_data, data_fetcher):
        self._user = user_data
        self._data_fetcher = data_fetcher
        self._name = f"Flatastic User {self._user['firstName']}"
        self._state = None

    @property
    def icon(self):
        return "mdi:account"

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return f"flatastic_user_{self._user['id']}"

    
    @property
    def state(self):
        user_id = str(self._user["id"])
        now = datetime.now()

        # Get tasks assigned to this user
        user_tasks = [t for t in self._data_fetcher.tasks if str(t.get("currentUser")) == user_id]

        # Count overdue tasks
        overdue_count = 0
        for task in user_tasks:
            rotation_time = int(task.get("rotationTime", 0))
            last_done = int(task.get("lastDoneDate", 0))

            if rotation_time == -1:
                continue

            next_due = last_done + rotation_time
            if now.timestamp() > next_due:
                overdue_count += 1

        if overdue_count == 0:
            return "No overdue tasks"
        elif overdue_count == 1:
            return "1 overdue task"
        else:
            return f"{overdue_count} overdue tasks"

    @property
    def extra_state_attributes(self):
        currency = self._data_fetcher.currency
        user_id = str(self._user["id"])
        tasks = [t for t in self._data_fetcher.tasks if str(t.get("currentUser")) == user_id]
        task_titles = [t["title"] for t in tasks]

        user_paid_flows = [f for f in self._data_fetcher.cashflow if str(f.get("paidBy")) == user_id]
        recent_flows = sorted(user_paid_flows, key=lambda f: f.get("date", 0), reverse=True)[:3]
        flow_info = [f"{f['name']}: {f['totalSum']} {currency}" for f in recent_flows]

        balance_entry = next((s for s in self._data_fetcher.statistics if str(s["id"]) == user_id), {})
        balance = balance_entry.get("balance", 0.0)

        return {
            "chore_points": self._user.get("chorePoints", 0),
            "balance": f"{balance:.2f} {currency}",
            "assigned_tasks": task_titles,
            "recent_cashflow": flow_info,
        }

    async def async_update(self):
        await self._data_fetcher.update_all()


class FlatasticTaskSensor(Entity):
    def __init__(self, task_data, data_fetcher):
        self._task = task_data
        self._data_fetcher = data_fetcher
        self._name = f"Flatastic {self._task.get('title', 'Unknown')}"
        self._state = None
        self._attributes = {}

    @property
    def icon(self):
        return "mdi:clipboard-check"

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return f"flatastic_task_{self._task['id']}"

    @property
    def state(self):
        return self._state or "Unknown"

    @property
    def extra_state_attributes(self):
        return self._attributes

    async def async_update(self):
        task = self._task
        user = self._data_fetcher.get_user_by_id(str(task.get("currentUser")))
        next_person = user.get("firstName") if user else "Unknown"

        rotation_time = int(task.get("rotationTime", 0))
        last_done = int(task.get("lastDoneDate", 0))
        rotation_time_days = round(rotation_time / 86400, 2) if rotation_time > 0 else None


        if rotation_time == -1:
            self._state = "If needed"
            self._attributes = {
                "title": task.get("title"),
                "next_person": next_person,
                "overdue": False,
                "periodicity_days": None,
                "points": int(task.get("points", 0)),
            }
        else:
            next_due_timestamp = last_done + rotation_time
            due_date = datetime.fromtimestamp(next_due_timestamp)
            overdue = datetime.now() > due_date
            self._state = "Overdue" if overdue else "Upcoming"
            self._attributes = {
                "title": task.get("title"),
                "next_person": next_person,
                "due_date": due_date.isoformat(),
                "overdue": overdue,
                "periodicity_days": rotation_time_days,
                "points": int(task.get("points", 0)),
            }


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
