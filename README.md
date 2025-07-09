<img src="https://raw.githubusercontent.com/avidoni/hass-flatastic/main/images/flatastic.png" alt="Flatastic Integration Logo" title="Flatastic" align="right" height="60" />

# Home Assistant Flatastic Integration

This custom integration connects the beloved german WG app [Flatastic](https://www.flatastic-app.com/) with [Home Assistant](https://www.home-assistant.io/). 

It displays some components of Flatastic as Sensors in Homeassistant and synchs the grocery list as a Todo!

---

[![Open Flatastic in your Home Assistant instance](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=avidoni&repository=hass-flatastic)

---

## Features

### User Sensors

Creates one **sensor per user** with the attributes:
- **Chore Points** – Total points earned from completed chores
- **Balance** – Money owed or owing
- **Assigned Tasks** – Tasks currently assigned to the user
- **Recent Cashflow** – Most recent payments or contributions

### Chore Sensors

Creates one **sensor per chore** with attributes:
- **Title** – Name of the chore
- **Next person** – Who is responsible next
- **Due date** – Date in a format usable for automations
- **Overdue** – Boolean flag indicating whether the chore is overdue
- **Periodicity** - Days until the task repeats
- **Points** – How many points the chore is worth

### Grocery List (To-Do Entity)

Creates a **to-do list** entity synced with your Flatastic shopping list. You can:
- Display items
- Add new items
- Delete items
- Toggle items as bought/unbought

---

## Installation

### 1. Add Repository via HACS
1. You should find it by searchin "Flatastic"
2. Click the install button!
3. If you want to, already reboot Homeassistant, or go to the next step



### 2. Get Your API Key
1. Log into [Flatastic WebApp](https://www.flatastic-app.com/webapp/)
2. In you browser, right click and open **Developer Tools → Network tab**
3. Push some buttons on the web app until you see a request going through that includes the header `x-api-key`
4. Copy the value of `x-api-key`

### 3. Configure Home Assistant

Add the following to your `configuration.yaml`:

```yaml
sensor:
  - platform: flatastic
    api_key: "your-x-api-key"

todo:
  - platform: flatastic
    api_key: "your-x-api-key"
````

** Restart Home Assistant after saving the file !!! **
---

## No Premium features used

This integration only uses features available in the free version of Flatastic because I do not have a subscription.

---

## Credits

Inspired by and in some regard using code by:

* [MMM-flatastic](https://github.com/joschi27/MMM-flatastic)
* [Robin Glauser’s dashboard project](https://www.robinglauser.ch/blog/2021/03/27/building-a-dashboard-in-a-pictureframe-for-my-flat/)

---

## License

MIT License – Free to use, modify, contribute

I have no association to Flatastic, this is a community made integration. This also means it might break at some point if Flatastic chooses to close certain API points.

---

This is my first integration. If you have some inputs or ideas, let me know! Remember that I am no professional and am doing this in my free time. Enjoy!

