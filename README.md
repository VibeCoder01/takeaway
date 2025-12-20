# Crown City Menu Picker

A realtime, browser-based menu picker for shared ordering. The UI is a single `index.html` file served by a lightweight `aiohttp` websocket server.

## Features
- Realtime shared session state with per-room people and carts
- Local allergen filters (per browser) with persistent selection
- Vegan-only and gluten-free-only filters stored in `localStorage`
- Multi-term search with AND/OR matching that expands matching sections
- Menu “Expand all” / “Close all” controls
- “Show ALL selected food.” modal with per-person collapse/expand controls

## Project Layout
- `index.html` — UI, styling, and client-side logic
- `server.py` — aiohttp server and websocket room/state handling

## Selections are Highlighted
<img width="1211" height="926" alt="image" src="https://github.com/user-attachments/assets/b4191106-ad67-4be4-90e7-85d8aaa38388" />

## Showing everyone's selections
<img width="1024" height="687" alt="image" src="https://github.com/user-attachments/assets/a4ab03a4-3156-4215-bdf3-a42c77013baa" />

## Searching
<img width="1208" height="883" alt="image" src="https://github.com/user-attachments/assets/ab4bd6d7-6a4e-4175-ba97-28353e97fc08" />

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
- The UI connects to the default room; room handling is still supported server-side.
- Allergen and diet filters are per-browser and stored in `localStorage`.
- Duplicate person names are blocked per room.
- The server logs key user actions with timestamps in the console.

## Filtering
- Open “Allergen key” and toggle allergens to exclude matching items.
- Use “Vegan only” or “Gluten-free only” to keep just those items.
- “Clear filters” resets both allergen and diet filters.
- Use search terms separated by spaces, then toggle AND/OR to control matching.

## Common Tasks
- Add a person: click “＋ Add person”
- Filter menu: open “Allergen key” and toggle allergens, Vegan only, or Gluten-free only

## License
MIT — see `LICENSE`.
