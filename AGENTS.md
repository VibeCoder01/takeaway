# Repository Guidelines

## Project Structure & Module Organization
- `index.html` contains the single-page UI, styling, and client-side logic for the realtime menu picker.
- `server.py` hosts the aiohttp server and websocket state sync logic.
- There are no separate asset or test directories; all assets are embedded in `index.html`.

## Build, Test, and Development Commands
- `python3 server.py` starts the local web server on `http://localhost:8080` and websocket endpoint at `/ws`.
- To preview just the static UI without websockets, open `index.html` directly in a browser.

## Coding Style & Naming Conventions
- Python: follow PEP 8 with 4-space indentation; keep functions small and explicit (`ws_handler`, `index_handler`).
- HTML/CSS/JS: 2-space indentation in `index.html`; use kebab-case for CSS classes (e.g., `cardhead`, `personTabs`) and camelCase for JS variables.
- Avoid introducing non-ASCII characters; keep strings plain and consistent with existing UI copy.

## Testing Guidelines
- No automated tests are present. If you add tests, place them in a new `tests/` directory and document the runner (e.g., `pytest`).
- Keep test names descriptive, such as `test_room_version_bumps_on_patch`.

## Commit & Pull Request Guidelines
- No Git history is available in this repo, so there is no established commit message convention.
- If you add commits, prefer concise, imperative messages (e.g., `Add websocket room key support`).
- PRs should include a short summary, steps to verify (`python3 server.py` + manual UI check), and screenshots for UI changes.

## Security & Configuration Tips
- `server.py` exposes `HOST`, `PORT`, and optional `ROOM_KEY`. Set `ROOM_KEY` to restrict room access.
- Avoid exposing the server directly to the public internet without additional authentication or reverse-proxy protection.
