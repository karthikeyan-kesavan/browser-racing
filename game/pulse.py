from __future__ import annotations

import math
import random
import secrets
import string
import threading
import time
from dataclasses import dataclass, field

from flask import current_app, request
from flask_socketio import SocketIO

NAMESPACE = "/pulse"
BASE_SPEED = 225.0
ARENA_RADIUS = 262.0
PARRY_RADIUS = 64.0
HIT_RADIUS = 21.0
COLORS = {
    "#69f3db", "#ff4f5f", "#ff9b42", "#59aaff", "#b1f569",
    "#b293ff", "#ff8ac7", "#e9f4ff", "#ffe29a", "#62718c",
}
MODELS = {"pulse", "robot", "bear", "fox", "dragon"}
ABILITIES = {"dash": 2.6, "shield": 8.0, "chain": 7.0, "freeze": 9.0,
             "slow": 8.0, "blink": 6.0, "power": 8.0}


@dataclass
class Loadout:
    name: str
    color: str = "#69f3db"
    model: str = "pulse"
    ability: str = "dash"


def parse_loadout(data: object) -> Loadout:
    if not isinstance(data, dict):
        raise ValueError("Send a player name and loadout.")
    name = data.get("name")
    color, model, ability = data.get("color"), data.get("model"), data.get("ability")
    if not isinstance(name, str) or not name.strip() or len(name) > 16 or not name.isprintable():
        raise ValueError("Your name must contain 1-16 printable characters.")
    if not isinstance(color, str) or color not in COLORS:
        raise ValueError("Choose a valid skin color.")
    if not isinstance(model, str) or model not in MODELS:
        raise ValueError("Choose a valid model.")
    if not isinstance(ability, str) or ability not in ABILITIES:
        raise ValueError("Choose a valid ability.")
    return Loadout(name.strip(), color, model, ability)


def number(data: dict, key: str, minimum: float, maximum: float) -> float:
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Invalid {key} input.")
    if not minimum <= value <= maximum or not math.isfinite(value):
        raise ValueError(f"Invalid {key} input.")
    return float(value)


@dataclass
class Actor:
    id: int
    name: str
    color: str
    model: str
    ability: str
    is_bot: bool
    x: float
    y: float
    facing: float
    alive: bool = True
    guard: float = 0
    cooldown: float = 0
    ability_cooldown: float = 0
    shield: float = 0
    power: float = 0
    dash_time: float = 0
    dash_x: float = 0
    dash_y: float = 0
    flash: float = 0
    bot_angle: float = 0
    bot_decision: bool = False
    bot_will_parry: bool = True
    mx: float = 0
    my: float = 0
    input_time: float = 0
    kills: int = 0
    parries: int = 0
    perfects: int = 0

    def snapshot(self) -> dict:
        return {
            "id": self.id, "name": self.name, "color": self.color, "model": self.model,
            "ability": self.ability, "isBot": self.is_bot, "x": self.x, "y": self.y,
            "facing": self.facing, "alive": self.alive, "guard": self.guard,
            "cooldown": self.cooldown, "abilityCooldown": self.ability_cooldown,
            "shield": self.shield, "power": self.power, "flash": self.flash,
            "kills": self.kills, "parries": self.parries, "perfects": self.perfects,
        }


@dataclass
class Ball:
    x: float = 0
    y: float = 0
    target: int = 0
    speed: float = BASE_SPEED
    last_defender: int = -1

    def snapshot(self) -> dict:
        return {"x": self.x, "y": self.y, "target": self.target,
                "speed": self.speed, "lastDefender": self.last_defender}


@dataclass
class Member:
    slot: int
    loadout: Loadout


@dataclass
class PulseRoom:
    code: str
    members: dict[str, Member] = field(default_factory=dict)
    host: str = ""
    actors: list[Actor] = field(default_factory=list)
    ball: Ball = field(default_factory=Ball)
    phase: str = "lobby"
    round: int = 0
    countdown: float = 0
    launch: float = 0
    elapsed: float = 0
    rally: int = 0
    freeze: float = 0
    slow: float = 0
    winner: int | None = None
    earned: dict[int, int] = field(default_factory=dict)
    victories: dict[int, int] = field(default_factory=dict)
    events: list[dict] = field(default_factory=list)
    serial: int = 0

    def add(self, sid: str, loadout: Loadout) -> Member:
        if self.phase not in {"lobby", "result"}:
            raise ValueError("This round has started. Join after it finishes.")
        occupied = {member.slot for member in self.members.values()}
        if len(occupied) >= 6:
            raise ValueError("This room is full.")
        slot = next(index for index in range(6) if index not in occupied)
        member = Member(slot, loadout)
        self.members[sid] = member
        self.earned[slot] = 0
        self.victories[slot] = 0
        if not self.host:
            self.host = sid
        return member

    def remove(self, sid: str) -> None:
        member = self.members.pop(sid)
        if self.actors and self.phase in {"countdown", "playing"}:
            actor = self.actors[member.slot]
            actor.is_bot = True
            actor.name = f"{actor.name} (BOT)"
            actor.mx = actor.my = 0
            actor.bot_angle = math.atan2(actor.y, actor.x)
            actor.bot_decision = False
        if self.host == sid:
            self.host = next(iter(self.members), "")

    def start(self) -> None:
        if self.phase not in {"lobby", "result"}:
            raise ValueError("A round is already running.")
        loadouts = {member.slot: member.loadout for member in self.members.values()}
        self.actors = []
        bot_names = ["NOVA", "FLUX", "ECHO", "VEX", "COMET", "ORBIT"]
        bot_colors = ["#b293ff", "#ff9b42", "#59aaff", "#ff8ac7", "#ffe29a", "#b1f569"]
        for slot in range(6):
            angle = math.pi / 2 + slot * math.pi / 3
            loadout = loadouts.get(slot, Loadout(bot_names[slot], bot_colors[slot]))
            self.actors.append(Actor(
                slot, loadout.name, loadout.color, loadout.model, loadout.ability,
                slot not in loadouts, math.cos(angle) * 205, math.sin(angle) * 205,
                angle + math.pi, bot_angle=angle,
            ))
        self.ball = Ball(target=self.members[self.host].slot)
        self.phase = "countdown"
        self.countdown = 3
        self.launch = self.elapsed = self.rally = self.freeze = self.slow = 0
        self.winner = None
        self.round += 1
        self.event("start", self.actors[self.ball.target], "GET READY")

    def event(self, kind: str, actor: Actor, message: str) -> None:
        self.serial += 1
        self.events.append({"serial": self.serial, "kind": kind, "actor": actor.id,
                            "x": actor.x, "y": actor.y, "color": actor.color, "message": message})
        self.events = self.events[-12:]

    def alive(self) -> list[Actor]:
        return [actor for actor in self.actors if actor.alive]

    def retarget(self, actor: Actor) -> None:
        for contender in self.actors:
            contender.guard = 0
        self.ball.target = actor.id
        actor.bot_decision = False
        actor.bot_will_parry = random.random() < max(.68, .94 - self.rally * .008)

    def parry(self, actor: Actor) -> bool:
        if self.phase != "playing" or not actor.alive or actor.cooldown > 0 or self.ball.target != actor.id:
            return False
        actor.guard = .25
        actor.cooldown = .8
        return True

    def ability(self, actor: Actor) -> bool:
        if self.phase != "playing" or not actor.alive or actor.ability_cooldown > 0:
            return False
        ability = actor.ability
        if ability == "chain" and self.ball.target == actor.id:
            return False
        actor.ability_cooldown = ABILITIES[ability]
        if ability == "dash":
            actor.dash_time = .16
            actor.dash_x, actor.dash_y = math.cos(actor.facing), math.sin(actor.facing)
        elif ability == "shield":
            actor.shield = 3
        elif ability == "chain":
            self.retarget(actor)
            self.launch = 0
        elif ability == "freeze":
            self.freeze = 1.5
        elif ability == "slow":
            self.slow = 3
        elif ability == "blink":
            actor.x += math.cos(actor.facing) * 100
            actor.y += math.sin(actor.facing) * 100
            self.clamp_actor(actor)
        elif ability == "power":
            actor.power = 6
        self.event("ability", actor, ability.upper())
        return True

    @staticmethod
    def clamp_actor(actor: Actor) -> None:
        radius = math.hypot(actor.x, actor.y)
        if radius > ARENA_RADIUS:
            actor.x *= ARENA_RADIUS / radius
            actor.y *= ARENA_RADIUS / radius

    def deflect(self, actor: Actor, separation: float) -> None:
        if self.phase != "playing" or not actor.alive or self.ball.target != actor.id:
            return
        shielded = actor.shield > 0 and actor.guard <= 0
        perfect = not shielded and separation < 40
        power = 100 if not shielded and actor.power > 0 else 0
        actor.guard = actor.shield = 0
        actor.flash = .3
        if not shielded:
            actor.power = 0
        if perfect:
            actor.cooldown = .25
            actor.perfects += 1
        actor.parries += 1
        self.rally += 1
        self.ball.speed = min(1080, self.ball.speed + (36 if perfect else 24) + power)
        self.ball.last_defender = actor.id
        others = [other for other in self.alive() if other.id != actor.id]
        target = random.choice(others) if actor.is_bot else max(
            others, key=lambda other: math.cos(math.atan2(other.y - actor.y, other.x - actor.x) - actor.facing)
        )
        self.retarget(target)
        message = "SHIELD RETURN" if shielded else "POWER RETURN" if power else "PERFECT RETURN" if perfect else "DEFLECTED"
        self.event("deflect", actor, message)

    def eliminate(self, actor: Actor) -> None:
        if self.phase != "playing" or not actor.alive:
            return
        actor.alive = False
        self.ball.speed = BASE_SPEED
        if self.ball.last_defender >= 0:
            defender = self.actors[self.ball.last_defender]
            if not defender.is_bot and defender.id in self.earned:
                defender.kills += 1
                self.earned[defender.id] += 20
        self.event("eliminate", actor, f"{actor.name} ELIMINATED")
        survivors = self.alive()
        if len(survivors) == 1:
            self.winner = survivors[0].id
            if not survivors[0].is_bot:
                self.earned[self.winner] += 60
                self.victories[self.winner] += 1
            self.phase = "result"
            return
        self.ball.x = self.ball.y = 0
        self.ball.last_defender = -1
        self.launch = .9
        self.retarget(random.choice(survivors))

    def move(self, dt: float) -> None:
        for actor in self.alive():
            for attribute in ("guard", "cooldown", "ability_cooldown", "shield", "power", "flash"):
                setattr(actor, attribute, max(0, getattr(actor, attribute) - dt))
            if actor.is_bot:
                actor.bot_angle += dt * (.19 if actor.id % 2 else -.17)
                radius = 170 + math.sin(self.elapsed * .8 + actor.id) * 35
                dx = math.cos(actor.bot_angle) * radius - actor.x
                dy = math.sin(actor.bot_angle) * radius - actor.y
                length = math.hypot(dx, dy)
                if length > 3:
                    actor.x += dx / length * 95 * dt
                    actor.y += dy / length * 95 * dt
                actor.facing = math.atan2(self.ball.y - actor.y, self.ball.x - actor.x)
                if self.ball.target == actor.id and self.launch <= 0 and self.freeze <= 0 and not actor.bot_decision:
                    speed = self.ball.speed * (.45 if self.slow > 0 else 1)
                    arrival = (math.hypot(actor.x - self.ball.x, actor.y - self.ball.y) - HIT_RADIUS) / speed
                    if arrival < .13:
                        actor.bot_decision = True
                        if actor.bot_will_parry:
                            self.parry(actor)
            elif actor.dash_time > 0:
                actor.x += actor.dash_x * 650 * dt
                actor.y += actor.dash_y * 650 * dt
                actor.dash_time = max(0, actor.dash_time - dt)
            elif self.elapsed - actor.input_time <= .5:
                length = max(1, math.hypot(actor.mx, actor.my))
                actor.x += actor.mx / length * 170 * dt
                actor.y += actor.my / length * 170 * dt
            self.clamp_actor(actor)

    def tick(self, dt: float) -> None:
        if self.phase == "countdown":
            self.countdown = max(0, self.countdown - dt)
            if self.countdown == 0:
                self.phase = "playing"
                self.launch = .55
            return
        remaining = dt
        while remaining > 0 and self.phase == "playing":
            step = min(remaining, 1 / 120)
            remaining -= step
            self.elapsed += step
            frozen, slowed = self.freeze > 0, self.slow > 0
            self.freeze = max(0, self.freeze - step)
            self.slow = max(0, self.slow - step)
            if self.launch > 0:
                self.launch = max(0, self.launch - step)
                self.move(step)
                continue
            self.move(step)
            if frozen:
                continue
            target = self.actors[self.ball.target]
            dx, dy = target.x - self.ball.x, target.y - self.ball.y
            length = math.hypot(dx, dy) or 1
            old_x, old_y = self.ball.x, self.ball.y
            speed = self.ball.speed * (.45 if slowed else 1)
            self.ball.x += dx / length * speed * step
            self.ball.y += dy / length * speed * step
            vx, vy = self.ball.x - old_x, self.ball.y - old_y
            squared = vx * vx + vy * vy
            progress = 0 if squared == 0 else max(0, min(1, ((target.x - old_x) * vx + (target.y - old_y) * vy) / squared))
            separation = math.hypot(old_x + vx * progress - target.x, old_y + vy * progress - target.y)
            if (target.guard > 0 or target.shield > 0) and separation <= PARRY_RADIUS:
                self.deflect(target, separation)
            elif separation <= HIT_RADIUS:
                self.eliminate(target)

    def snapshot(self) -> dict:
        return {
            "code": self.code, "phase": self.phase, "round": self.round,
            "host": self.members[self.host].slot,
            "members": [{"slot": member.slot, "name": member.loadout.name} for member in self.members.values()],
            "actors": [actor.snapshot() for actor in self.actors], "ball": self.ball.snapshot(),
            "countdown": self.countdown, "launch": self.launch, "time": self.elapsed,
            "rally": self.rally, "freeze": self.freeze, "slow": self.slow, "winner": self.winner,
            "earned": self.earned, "victories": self.victories,
            "events": self.events, "serial": self.serial,
        }


class PulseHub:
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.rooms: dict[str, PulseRoom] = {}
        self.connections: dict[str, str] = {}
        self.lock = threading.RLock()
        self.running = False

    def room_for(self, sid: str) -> PulseRoom:
        if sid not in self.connections:
            raise ValueError("Join a room first.")
        return self.rooms[self.connections[sid]]

    def broadcast(self, room: PulseRoom) -> None:
        self.socketio.emit("pulse_state", room.snapshot(), namespace=NAMESPACE, to=room.code)

    def leave(self, sid: str) -> None:
        code = self.connections.pop(sid, None)
        if code is None:
            return
        room = self.rooms[code]
        self.socketio.server.leave_room(sid, code, namespace=NAMESPACE)
        room.remove(sid)
        if not room.members:
            del self.rooms[code]
        else:
            self.broadcast(room)

    def tick(self, dt: float) -> None:
        with self.lock:
            for room in self.rooms.values():
                if room.phase in {"countdown", "playing"}:
                    room.tick(dt)
                    self.broadcast(room)

    def loop(self) -> None:
        previous = time.monotonic()
        while True:
            self.socketio.sleep(1 / 30)
            now = time.monotonic()
            self.tick(min(.1, now - previous))
            previous = now

    def command(self, sid: str, command: str, data: object) -> dict:
        with self.lock:
            if command in {"create", "join"}:
                loadout = parse_loadout(data)
                if not isinstance(data, dict):
                    raise ValueError("Invalid room request.")
                if sid in self.connections:
                    raise ValueError("Leave your current room first.")
                if command == "create":
                    if len(self.rooms) >= 64:
                        raise ValueError("The server is full. Try again later.")
                    code = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
                    while code in self.rooms:
                        code = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
                    room = PulseRoom(code)
                else:
                    code = data.get("code")
                    if not isinstance(code, str) or len(code.strip()) != 6:
                        raise ValueError("Enter a six-character room code.")
                    code = code.strip().upper()
                    if code not in self.rooms:
                        raise ValueError("Room not found. Check the code or ask your friend to create one.")
                    room = self.rooms[code]
                member = room.add(sid, loadout)
                self.rooms[code] = room
                self.connections[sid] = code
                self.socketio.server.enter_room(sid, code, namespace=NAMESPACE)
                self.broadcast(room)
                if not self.running:
                    self.running = True
                    self.socketio.start_background_task(self.loop)
                return {"ok": True, "you": member.slot, "state": room.snapshot()}
            if command == "leave":
                self.leave(sid)
                return {"ok": True}
            room = self.room_for(sid)
            member = room.members[sid]
            if command == "start":
                if room.host != sid:
                    raise ValueError("Only the room host can start a round.")
                room.start()
                self.broadcast(room)
            elif command == "loadout":
                if room.phase not in {"lobby", "result"}:
                    raise ValueError("Change your online loadout between rounds.")
                member.loadout = parse_loadout(data)
                self.broadcast(room)
            elif command == "input":
                if not isinstance(data, dict):
                    raise ValueError("Invalid movement input.")
                mx, my = number(data, "x", -1, 1), number(data, "y", -1, 1)
                facing = number(data, "facing", -math.tau * 100, math.tau * 100)
                if room.phase == "playing":
                    actor = room.actors[member.slot]
                    actor.mx, actor.my, actor.facing = mx, my, math.remainder(facing, math.tau)
                    actor.input_time = room.elapsed
            elif command == "action":
                if not isinstance(data, dict) or data.get("action") not in {"parry", "ability"}:
                    raise ValueError("Choose parry or ability.")
                if room.phase != "playing":
                    raise ValueError("Wait for the round to start.")
                actor = room.actors[member.slot]
                accepted = room.parry(actor) if data["action"] == "parry" else room.ability(actor)
                if not accepted:
                    raise ValueError("Not ready: check your target, cooldown, or eliminated status.")
            else:
                raise ValueError("Unknown room command.")
            return {"ok": True}


def register_pulse(socketio: SocketIO) -> PulseHub:
    hub = PulseHub(socketio)

    @socketio.on("pulse_command", namespace=NAMESPACE)
    def handle_command(data: object = None) -> dict:
        if not isinstance(data, dict) or not isinstance(data.get("command"), str):
            return {"ok": False, "error": "Invalid room command."}
        try:
            return hub.command(request.sid, data["command"], data.get("data"))
        except ValueError as error:
            current_app.logger.warning("Pulse room request rejected: %s", error)
            return {"ok": False, "error": str(error)}

    @socketio.on("connect", namespace=NAMESPACE)
    def connect() -> None:
        pass

    @socketio.on("disconnect", namespace=NAMESPACE)
    def disconnect() -> None:
        with hub.lock:
            hub.leave(request.sid)

    return hub
