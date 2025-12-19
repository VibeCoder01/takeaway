# Crown City Menu Picker

A realtime, browser-based menu picker for shared ordering. The UI is a single `index.html` file served by a lightweight `aiohttp` websocket server.

## Features
- Realtime shared room state with per-room people and carts
- Local allergen filters (per browser) with persistent selection
- Vegan-only and gluten-free-only filters stored in `localStorage`
- Room history dropdown saved in `localStorage`
- “Show ALL selected food.” modal with per-person collapse/expand controls

## Project Layout
- `index.html` — UI, styling, and client-side logic
- `server.py` — aiohttp server and websocket room/state handling

## Requirements
- Python 3.9+ recommended
- `aiohttp`

## Setup
```bash
python3 -m pip install aiohttp
```

## Run Locally
```bash
python3 server.py
```
Then open:
- `http://localhost:8080` in a browser

## Usage Notes
- Rooms are in-memory only; restarting the server clears all rooms.
- The room name is set in the header. Changing it reconnects automatically.
- Allergen and diet filters are per-browser and stored in `localStorage`.
- Duplicate person names are blocked per room.

## Filtering
- Open “Allergen key” and toggle allergens to exclude matching items.
- Use “Vegan only” or “Gluten-free only” to keep just those items.
- “Clear filters” resets both allergen and diet filters.

## Common Tasks
- Add a person: click “＋ Add person”
- Switch rooms: use the room input or “Recent rooms” dropdown
- Delete a room: click “Delete room” (clears it for everyone)
- Filter menu: open “Allergen key” and toggle allergens, Vegan only, or Gluten-free only

## License
MIT — see `LICENSE`.
