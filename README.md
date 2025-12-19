# Crown City Menu Picker

A realtime, browser-based menu picker for shared ordering. The UI is a single `index.html` file served by a lightweight `aiohttp` websocket server.

## Features
- Realtime shared room state with per-room people and carts
- Local allergen filters (per browser) with persistent selection
- Room history dropdown saved in `localStorage`
- “Show ALL selected food.” modal with expandable person sections

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
- Allergen filters are per-browser and stored in `localStorage`.

## Common Tasks
- Add a person: click “＋ Add person”
- Switch rooms: use the room input or “Recent rooms” dropdown
- Delete a room: click “Delete room” (clears it for everyone)

## License
MIT — see `LICENSE`.
