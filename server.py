#!/usr/bin/env python3
import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Dict, Any, Set, Optional

from aiohttp import web, WSMsgType

HOST = "0.0.0.0"
PORT = 8080

# Optional shared room key. Leave "" for none.
ROOM_KEY = ""  # e.g. "letmein"


@dataclass
class Room:
    clients: Set[web.WebSocketResponse] = field(default_factory=set)
    state: Dict[str, Any] = field(default_factory=dict)
    version: int = 1
    updated_at: float = field(default_factory=time.time)


rooms: Dict[str, Room] = {}


def default_state() -> Dict[str, Any]:
    return {
        "people": [],
        "activePersonId": None,
        "ui": {"search": ""},
    }


def get_room(room_id: str) -> Room:
    rid = (room_id or "default").strip()[:40] or "default"
    if rid not in rooms:
        rooms[rid] = Room(state=default_state(), version=1)
    return rooms[rid]


def full_state_msg(room_id: str, room: Room) -> Dict[str, Any]:
    return {
        "type": "full_state",
        "room": room_id,
        "version": room.version,
        "state": room.state,
        "serverTime": time.time(),
    }


def apply_patch(room: Room, patch: Dict[str, Any]):
    # Patch format: { "op": "set_state", "state": {...} }
    if not isinstance(patch, dict) or patch.get("op") != "set_state":
        raise ValueError("Unsupported patch op")
    new_state = patch.get("state")
    if not isinstance(new_state, dict):
        raise ValueError("state must be an object")
    if "people" not in new_state or not isinstance(new_state["people"], list):
        raise ValueError("Invalid people")
    if "activePersonId" not in new_state:
        raise ValueError("Missing activePersonId")
    names = [str(p.get("name", "")).strip().lower() for p in new_state["people"] if isinstance(p, dict)]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate person names are not allowed")

    room.state = new_state
    room.version += 1
    room.updated_at = time.time()


async def broadcast(room: Room, payload: Dict[str, Any], exclude: Optional[web.WebSocketResponse] = None):
    dead = []
    for ws in list(room.clients):
        if ws is exclude:
            continue
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        room.clients.discard(ws)


async def ws_handler(request: web.Request):
    ws = web.WebSocketResponse(max_msg_size=2_000_000)
    await ws.prepare(request)

    room_id = "default"
    room: Optional[Room] = None

    try:
        first = await ws.receive()

        if first.type != WSMsgType.TEXT:
            await ws.send_json({"type": "error", "error": "First message must be join (text)"})
            await ws.close()
            return ws

        try:
            obj = json.loads(first.data)
        except Exception:
            await ws.send_json({"type": "error", "error": "Bad JSON"})
            await ws.close()
            return ws

        if obj.get("type") != "join":
            await ws.send_json({"type": "error", "error": "First message must be join"})
            await ws.close()
            return ws

        room_id = (obj.get("room") or "default").strip()[:40] or "default"
        key = obj.get("key") or ""

        if ROOM_KEY and key != ROOM_KEY:
            await ws.send_json({"type": "error", "error": "Bad room key"})
            await ws.close()
            return ws

        room = get_room(room_id)
        room.clients.add(ws)

        await ws.send_json(full_state_msg(room_id, room))

        async for msg in ws:
            if msg.type != WSMsgType.TEXT:
                continue

            try:
                obj = json.loads(msg.data)
            except Exception:
                await ws.send_json({"type": "error", "error": "Bad JSON"})
                continue

            t = obj.get("type")

            if t == "request_full_state":
                await ws.send_json(full_state_msg(room_id, room))
                continue

            if t == "patch":
                base_version = int(obj.get("baseVersion") or 0)
                if base_version != room.version:
                    await ws.send_json({**full_state_msg(room_id, room), "note": "Version mismatch, resync"})
                    continue

                patch = obj.get("patch")
                try:
                    apply_patch(room, patch)
                except Exception as e:
                    await ws.send_json({"type": "error", "error": f"Patch rejected: {e}"})
                    continue

                await broadcast(room, full_state_msg(room_id, room))

            elif t == "delete_room":
                if room_id in rooms:
                    await broadcast(room, {"type": "room_deleted", "room": room_id})
                    for client in list(room.clients):
                        try:
                            await client.close()
                        except Exception:
                            pass
                    del rooms[room_id]
                return ws

            else:
                await ws.send_json({"type": "error", "error": "Unknown message type"})

    finally:
        if room is not None:
            room.clients.discard(ws)

    return ws


async def index_handler(request: web.Request):
    return web.FileResponse("index.html")


def main():
    app = web.Application()
    app.router.add_get("/", index_handler)
    app.router.add_get("/ws", ws_handler)
    web.run_app(app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()
