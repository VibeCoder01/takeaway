#!/usr/bin/env python3
import asyncio
import copy
import json
import time
from datetime import datetime
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


def log_action(action: str, status: str, detail: str = "") -> None:
    ts = datetime.now().isoformat(timespec="seconds")
    if detail:
        print(f"[{ts}] {action} | {status} | {detail}")
    else:
        print(f"[{ts}] {action} | {status}")


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


def describe_patch(old: Dict[str, Any], new: Dict[str, Any]) -> str:
    old_people = {p.get("id"): p for p in old.get("people", []) if isinstance(p, dict)}
    new_people = {p.get("id"): p for p in new.get("people", []) if isinstance(p, dict)}

    added = [p for pid, p in new_people.items() if pid not in old_people]
    removed = [p for pid, p in old_people.items() if pid not in new_people]
    renamed = []
    cart_changes = 0
    cart_detail = []

    for pid, p in new_people.items():
        if pid not in old_people:
            continue
        old_p = old_people[pid]
        if str(old_p.get("name", "")).strip() != str(p.get("name", "")).strip():
            renamed.append((old_p.get("name", ""), p.get("name", "")))

        old_cart = old_p.get("cart") or {}
        new_cart = p.get("cart") or {}
        keys = set(old_cart.keys()) | set(new_cart.keys())
        person_name = str(p.get("name", "")).strip() or "unknown"
        for key in keys:
            old_qty = int(old_cart.get(key) or 0)
            new_qty = int(new_cart.get(key) or 0)
            if old_qty != new_qty:
                cart_changes += 1
                cart_detail.append(f"{person_name}:{key}:{old_qty}->{new_qty}")

    active_old = old.get("activePersonId")
    active_new = new.get("activePersonId")
    active_change = active_old != active_new

    parts = []
    if added:
        names = ",".join([str(p.get("name", "")).strip() or "unknown" for p in added])
        parts.append(f"people_added={len(added)}({names})")
    if removed:
        names = ",".join([str(p.get("name", "")).strip() or "unknown" for p in removed])
        parts.append(f"people_removed={len(removed)}({names})")
    if renamed:
        parts.append(f"people_renamed={len(renamed)}")
    if active_change:
        parts.append(f"active_changed={active_new}")
    if cart_changes:
        parts.append(f"cart_changes={cart_changes}")
        if cart_detail:
            parts.append(f"cart_detail={','.join(cart_detail)}")

    return " ".join(parts) if parts else "no_change"


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
    client = request.remote or "unknown"

    try:
        first = await ws.receive()

        if first.type != WSMsgType.TEXT:
            log_action("join", "rejected", f"client={client} reason=non_text_first")
            await ws.send_json({"type": "error", "error": "First message must be join (text)"})
            await ws.close()
            return ws

        try:
            obj = json.loads(first.data)
        except Exception:
            log_action("join", "rejected", f"client={client} reason=bad_json")
            await ws.send_json({"type": "error", "error": "Bad JSON"})
            await ws.close()
            return ws

        if obj.get("type") != "join":
            log_action("join", "rejected", f"client={client} reason=not_join")
            await ws.send_json({"type": "error", "error": "First message must be join"})
            await ws.close()
            return ws

        room_id = (obj.get("room") or "default").strip()[:40] or "default"
        key = obj.get("key") or ""

        if ROOM_KEY and key != ROOM_KEY:
            log_action("join", "rejected", f"client={client} room={room_id} reason=bad_key")
            await ws.send_json({"type": "error", "error": "Bad room key"})
            await ws.close()
            return ws

        room = get_room(room_id)
        room.clients.add(ws)
        log_action("join", "ok", f"client={client} room={room_id}")

        await ws.send_json(full_state_msg(room_id, room))

        async for msg in ws:
            if msg.type != WSMsgType.TEXT:
                continue

            try:
                obj = json.loads(msg.data)
            except Exception:
                log_action("message", "rejected", f"client={client} room={room_id} reason=bad_json")
                await ws.send_json({"type": "error", "error": "Bad JSON"})
                continue

            t = obj.get("type")

            if t == "request_full_state":
                log_action("request_full_state", "ok", f"client={client} room={room_id}")
                await ws.send_json(full_state_msg(room_id, room))
                continue

            if t == "patch":
                base_version = int(obj.get("baseVersion") or 0)
                if base_version != room.version:
                    log_action(
                        "patch",
                        "rejected",
                        f"client={client} room={room_id} reason=version_mismatch",
                    )
                    await ws.send_json({**full_state_msg(room_id, room), "note": "Version mismatch, resync"})
                    continue

                patch = obj.get("patch")
                try:
                    old_state = copy.deepcopy(room.state)
                    apply_patch(room, patch)
                except Exception as e:
                    log_action("patch", "rejected", f"client={client} room={room_id} reason={e}")
                    await ws.send_json({"type": "error", "error": f"Patch rejected: {e}"})
                    continue

                detail = describe_patch(old_state, room.state)
                log_action("patch", "ok", f"client={client} room={room_id} {detail}")
                await broadcast(room, full_state_msg(room_id, room))

            elif t == "delete_room":
                log_action("delete_room", "ok", f"client={client} room={room_id}")
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
                log_action("message", "rejected", f"client={client} room={room_id} reason=unknown_type")
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
