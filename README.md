
# 🏡 Home Assistant Flatastic Integration

This custom integration connects your [Flatastic](https://www.flatastic-app.com/) shared living group with [Home Assistant](https://www.home-assistant.io/). 

It brings real-time data from Flatastic into Home Assistant and allows interaction with chores and the shopping list.

---

## ✨ Features

### 👤 User Sensors

Creates one **sensor per user** with the following attributes:
- **ChorePoints** – Total points earned from completed chores
- **Balance** – Money owed or owing
- **AssignedTasks** – Tasks currently assigned to the user
- **RecentCashflow** – Most recent payments or contributions

### 🧹 Chore Sensors

Creates one **sensor per chore** with attributes:
- **Title** – Name of the chore (e.g. `Papiersammlung`)
- **Next person** – Who is responsible next
- **Due date** – Date in a format usable for automations
- **Overdue** – Boolean flag indicating whether the chore is overdue
- **Points** – How many points the chore is worth

### 🛒 Grocery List (To-Do Entity)

Creates a **to-do list** entity synced with your Flatastic shopping list. You can:
- ✅ Display items
- ➕ Add new items
- ❌ Delete items
- 🔄 Toggle items as bought/unbought

---

## 🛠 Installation

### 1. Add Repository via HACS
1. Go to HACS → Integrations → Menu (⋮) → **Custom repositories**
2. Add this repository URL and select **Integration**
3. Install the integration

### 2. Get Your API Key
1. Log into [Flatastic WebApp](https://www.flatastic-app.com/webapp/)
2. Open **Developer Tools → Network tab**
3. Reload the page and find a request with the header `x-api-key`
4. Copy the value of `x-api-key`

### 3. Configure Home Assistant

Add the following to your `configuration.yaml`:

```yaml
sensor:
  - platform: hass-flatastic
    api_key: "yourAPIkey"

todo:
  - platform: hass-flatastic
    api_key: "yourAPIkey"
````

Restart Home Assistant after saving the file.

---

## 🔒 No Premium Required

This integration works with the free version of Flatastic. No premium features are used.

---

## 🙏 Credits

Inspired by:

* [MMM-flatastic](https://github.com/joschi27/MMM-flatastic)
* [Robin Glauser’s dashboard project](https://www.robinglauser.ch/blog/2021/03/27/building-a-dashboard-in-a-pictureframe-for-my-flat/)

---

## 📎 License

MIT License – Free to use, modify, and contribute.

