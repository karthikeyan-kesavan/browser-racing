from __future__ import annotations

import os
import random
import time
import uuid

from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24)
socketio = SocketIO(app, cors_allowed_origins="*")

WORLD_WIDTH = 3200
WORLD_HEIGHT = 2200
CHEST_COUNT = 90
CHEST_PICKUP_RADIUS = 54
LOBBY_WAIT_SECONDS = 15
BOT_CHOICE_DELAY_SECONDS = 0.35
BATTLE_TIMEOUT_SECONDS = 4
BATTLE_COOLDOWN_SECONDS = 1.5
MIN_MATCH_SIZE = 50
MAX_MATCH_SIZE = 100
BASE_OPTIONS = ["rock", "paper", "scissors"]
RARITY_ORDER = ["common", "uncommon", "rare", "epic", "legendary"]
RARITY_WEIGHTS = {
    "common": 100,
    "uncommon": 50,
    "rare": 25,
    "epic": 5,
    "legendary": 1,
}

OPTION_CATALOG = {
    "rock": {"rarity": "common", "beats": ["scissors", "chair", "wizard", "robot"]},
    "paper": {"rarity": "common", "beats": ["rock", "chair", "dragon"]},
    "scissors": {"rarity": "common", "beats": ["paper", "lion", "vampire"]},
    "chair": {"rarity": "common", "beats": ["lion", "vampire", "dragon"]},
    "lion": {"rarity": "uncommon", "beats": ["robot", "chair", "cactus"]},
    "ufo": {"rarity": "uncommon", "beats": ["dragon", "t-rex", "robot"]},
    "t-rex": {"rarity": "rare", "beats": ["ufo", "wizard", "lion"]},
    "robot": {"rarity": "rare", "beats": ["chair", "vampire", "paper"]},
    "dragon": {"rarity": "epic", "beats": ["robot", "ufo", "scissors"]},
    "wizard": {"rarity": "epic", "beats": ["robot", "chair", "t-rex"]},
    "vampire": {"rarity": "epic", "beats": ["wizard", "lion", "paper"]},
    "cactus": {"rarity": "common", "beats": ["robot", "wizard"]},
    "asteroid": {"rarity": "rare", "beats": ["ufo", "dragon"]},
    "samurai": {"rarity": "rare", "beats": ["vampire", "wizard"]},
    "dinosaur": {"rarity": "rare", "beats": ["chair", "rock"]},
    "spaceship": {"rarity": "epic", "beats": ["dragon", "asteroid", "robot"]},
    "phoenix": {"rarity": "legendary", "beats": ["wizard", "vampire", "robot"]},
    "kraken": {"rarity": "legendary", "beats": ["dragon", "spaceship", "samurai"]},
    "droid": {"rarity": "uncommon", "beats": ["chair", "cactus"]},
    "sword": {"rarity": "common", "beats": ["chair", "wizard"]},
    "shield": {"rarity": "common", "beats": ["lion", "vampire"]},
    "thunder": {"rarity": "epic", "beats": ["ufo", "dragon", "spaceship"]},
    "titan": {"rarity": "legendary", "beats": ["phoenix", "kraken", "thunder"]},
}

STATE = {
    "lobby": {},
    "players": {},
    "battle": None,
    "countdown_started": False,
    "match_started": False,
    "target_count": MIN_MATCH_SIZE,
    "chests": [],
}


def create_player(player_id, sid, is_bot=False, display_name=None):
    if display_name is None:
        name = f"BOT-{random.randint(100, 9999)}" if is_bot else f"PLAYER-{random.randint(100, 9999)}"
    else:
        name = display_name
    return {
        "id": player_id,
        "sid": sid,
        "name": name,
        "x": random.randint(80, WORLD_WIDTH - 80),
        "y": random.randint(80, WORLD_HEIGHT - 80),
        "alive": True,
        "in_battle": False,
        "battle_cooldown_until": 0,
        "is_bot": is_bot,
        "extras": [],
        "input": {"up": False, "down": False, "left": False, "right": False},
        "speed": 4.5 if is_bot else 6.0,
        "color": random.choice(["#00c2ff", "#ffd166", "#ff6b6b", "#90be6d", "#9b5de5", "#f15bb5"]),
    }


def create_chests():
    return [
        {
            "id": f"chest-{uuid.uuid4().hex[:8]}",
            "x": random.randint(80, WORLD_WIDTH - 80),
            "y": random.randint(80, WORLD_HEIGHT - 80),
        }
        for _ in range(CHEST_COUNT)
    ]


def get_inventory(player):
    inventory = list(BASE_OPTIONS)
    inventory.extend(player.get("extras", []))
    return inventory


def rarity_roll():
    weights = [RARITY_WEIGHTS[r] for r in RARITY_ORDER]
    return random.choices(RARITY_ORDER, weights=weights, k=1)[0]


def loot_option():
    rarity = rarity_roll()
    choices = [name for name, info in OPTION_CATALOG.items() if info["rarity"] == rarity and name not in BASE_OPTIONS]
    if not choices:
        return random.choice(["chair", "lion", "ufo", "t-rex", "dragon"])
    return random.choice(choices)


def beats(option_name):
    return OPTION_CATALOG.get(option_name, {}).get("beats", [])


def choose_winner(left_choice, right_choice):
    if left_choice == right_choice:
        return "tie"
    if right_choice in beats(left_choice):
        return "left"
    return "right"


def consume_if_extra(player, option_name):
    if option_name in BASE_OPTIONS:
        return
    player["extras"] = [item for item in player["extras"] if item != option_name]


def emit_world_state():
    payload = {
        "players": [
            {
                "id": player["id"],
                "name": player["name"],
                "x": player["x"],
                "y": player["y"],
                "alive": player["alive"],
                "is_bot": player["is_bot"],
                "inventory": get_inventory(player),
                "color": player["color"],
            }
            for player in STATE["players"].values()
        ],
        "chests": STATE["chests"],
        "world_width": WORLD_WIDTH,
        "world_height": WORLD_HEIGHT,
        "battle": STATE["battle"],
        "match_started": STATE["match_started"],
        "target_count": STATE["target_count"],
    }
    socketio.emit("world_state", payload)


def fill_bots_to_target():
    while len(STATE["lobby"]) < STATE["target_count"]:
        bot_id = f"bot-{uuid.uuid4().hex[:8]}"
        STATE["lobby"][bot_id] = create_player(bot_id, bot_id, is_bot=True)


def start_match():
    if STATE["match_started"] or not STATE["lobby"]:
        return

    STATE["target_count"] = min(MAX_MATCH_SIZE, max(MIN_MATCH_SIZE, len(STATE["lobby"])))
    fill_bots_to_target()
    STATE["players"] = dict(STATE["lobby"])
    STATE["chests"] = create_chests()
    STATE["match_started"] = True

    for player in STATE["players"].values():
        player["alive"] = True
        player["in_battle"] = False

    for player in STATE["players"].values():
        if player["sid"]:
            socketio.emit(
                "match_start",
                {
                    "player_id": player["id"],
                    "target_count": STATE["target_count"],
                    "world_width": WORLD_WIDTH,
                    "world_height": WORLD_HEIGHT,
                },
                room=player["sid"],
            )

    emit_world_state()
    socketio.start_background_task(game_loop)


def start_battle(player_a, player_b):
    now = time.monotonic()
    if (
        player_a["in_battle"]
        or player_b["in_battle"]
        or player_a["battle_cooldown_until"] > now
        or player_b["battle_cooldown_until"] > now
    ):
        return
    player_a["in_battle"] = True
    player_b["in_battle"] = True
    STATE["battle"] = {
        "players": [player_a["id"], player_b["id"]],
        "choices": {},
        "bot_choice_at": time.monotonic() + BOT_CHOICE_DELAY_SECONDS,
        "timeout_at": time.monotonic() + BATTLE_TIMEOUT_SECONDS,
    }
    for pid in [player_a["id"], player_b["id"]]:
        player = STATE["players"].get(pid)
        if not player:
            continue
        socketio.emit(
            "battle_start",
            {
                "opponent": player_b["name"] if pid == player_a["id"] else player_a["name"],
                "options": get_inventory(player),
            },
            room=player["sid"],
        )
    emit_world_state()


def resolve_battle():
    battle = STATE["battle"]
    if not battle or len(battle["choices"]) < 2:
        return

    p1_id, p2_id = battle["players"]
    p1 = STATE["players"].get(p1_id)
    p2 = STATE["players"].get(p2_id)
    if not p1 or not p2:
        STATE["battle"] = None
        return

    choice_a = battle["choices"].get(p1_id)
    choice_b = battle["choices"].get(p2_id)
    if not choice_a or not choice_b:
        return

    winner = choose_winner(choice_a, choice_b)
    result_message = "Tie! No one is eliminated."

    if winner == "left":
        result_message = f"{p1['name']} wins the duel!"
        p2["alive"] = False
    elif winner == "right":
        result_message = f"{p2['name']} wins the duel!"
        p1["alive"] = False

    consume_if_extra(p1, choice_a)
    consume_if_extra(p2, choice_b)
    p1["in_battle"] = False
    p2["in_battle"] = False
    cooldown_until = time.monotonic() + BATTLE_COOLDOWN_SECONDS
    p1["battle_cooldown_until"] = cooldown_until
    p2["battle_cooldown_until"] = cooldown_until

    for pid in [p1_id, p2_id]:
        player = STATE["players"].get(pid)
        if not player:
            continue
        socketio.emit(
            "battle_result",
            {
                "winner": winner,
                "message": result_message,
                "choice_a": choice_a,
                "choice_b": choice_b,
            },
            room=player["sid"],
        )

    STATE["battle"] = None
    alive_players = [player for player in STATE["players"].values() if player["alive"]]
    if len(alive_players) <= 1:
        final_winner = alive_players[0]["name"] if alive_players else "Nobody"
        for player in STATE["players"].values():
            socketio.emit("match_end", {"winner": final_winner}, room=player["sid"])
        STATE["players"] = {}
        STATE["lobby"] = {}
        STATE["match_started"] = False
        STATE["countdown_started"] = False
    else:
        emit_world_state()


def distance_between(a, b):
    return ((a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2) ** 0.5


def game_loop():
    while STATE["match_started"]:
        time.sleep(0.05)
        if not STATE["match_started"]:
            return

        for player in STATE["players"].values():
            if not player["alive"] or player["in_battle"]:
                continue
            if player["is_bot"]:
                targets = [
                    target for target in STATE["players"].values()
                    if target["id"] != player["id"]
                    and target["alive"]
                    and not target["in_battle"]
                    and target["battle_cooldown_until"] <= time.monotonic()
                ]
                target = min(targets, key=lambda item: distance_between(player, item), default=None)
                if target and distance_between(player, target) > 44:
                    dx = target["x"] - player["x"]
                    dy = target["y"] - player["y"]
                    length = (dx ** 2 + dy ** 2) ** 0.5 or 1
                    player["x"] += (dx / length) * player["speed"]
                    player["y"] += (dy / length) * player["speed"]
                else:
                    player["x"] += random.randint(-1, 1) * 2
                    player["y"] += random.randint(-1, 1) * 2
                player["x"] = max(20, min(WORLD_WIDTH - 20, player["x"]))
                player["y"] = max(20, min(WORLD_HEIGHT - 20, player["y"]))
                continue

            dx = (1 if player["input"]["right"] else 0) - (1 if player["input"]["left"] else 0)
            dy = (1 if player["input"]["down"] else 0) - (1 if player["input"]["up"] else 0)
            if dx != 0 or dy != 0:
                length = (dx ** 2 + dy ** 2) ** 0.5
                player["x"] += (dx / length) * player["speed"]
                player["y"] += (dy / length) * player["speed"]
                player["x"] = max(20, min(WORLD_WIDTH - 20, player["x"]))
                player["y"] = max(20, min(WORLD_HEIGHT - 20, player["y"]))

            for chest in STATE["chests"][:]:
                if distance_between(player, chest) <= CHEST_PICKUP_RADIUS and len(player["extras"]) < 3:
                    option = loot_option()
                    if option in player["extras"]:
                        alternatives = [name for name in OPTION_CATALOG if name not in BASE_OPTIONS and name not in player["extras"]]
                        option = random.choice(alternatives)
                    player["extras"].append(option)
                    STATE["chests"].remove(chest)
                    socketio.emit("toast", {"message": f"Chest collected! You gained {option}"}, room=player["sid"])
                    break

        players = [
            player for player in STATE["players"].values()
            if player["alive"]
            and not player["in_battle"]
            and player["battle_cooldown_until"] <= time.monotonic()
        ]
        for i in range(len(players)):
            for j in range(i + 1, len(players)):
                a = players[i]
                b = players[j]
                if distance_between(a, b) < 52:
                    start_battle(a, b)
                    break
            if STATE["battle"]:
                break

        battle = STATE["battle"]
        if battle and time.monotonic() >= battle["bot_choice_at"]:
            for battle_player_id in battle["players"]:
                battle_player = STATE["players"].get(battle_player_id)
                if battle_player and battle_player["is_bot"] and battle_player_id not in battle["choices"]:
                    battle["choices"][battle_player_id] = random.choice(get_inventory(battle_player))
        if battle and time.monotonic() >= battle["timeout_at"]:
            for battle_player_id in battle["players"]:
                battle_player = STATE["players"].get(battle_player_id)
                if battle_player and battle_player_id not in battle["choices"]:
                    battle["choices"][battle_player_id] = random.choice(get_inventory(battle_player))
        if battle and len(battle["choices"]) >= 2:
            resolve_battle()

        emit_world_state()


def lobby_start_timer():
    socketio.sleep(LOBBY_WAIT_SECONDS)
    if STATE["match_started"] or not STATE["lobby"]:
        STATE["countdown_started"] = False
        return
    STATE["countdown_started"] = False
    start_match()


@app.route("/")
def index():
    return render_template("car_game.html")


@app.route("/health")
def health():
    return {"status": "ok"}


@socketio.on("connect")
def handle_connect():
    player_id = str(uuid.uuid4())
    session["player_id"] = player_id
    emit("player_id", {"player_id": player_id})
    emit("lobby_status", {"count": len(STATE["lobby"])})


@socketio.on("join_lobby")
def handle_join_lobby():
    player_id = session.get("player_id")
    if not player_id:
        return
    if STATE["match_started"]:
        if player_id not in STATE["players"] and len(STATE["players"]) < MAX_MATCH_SIZE:
            player = create_player(player_id, request.sid)
            STATE["players"][player_id] = player
            emit("joined_lobby", {"count": len(STATE["players"]), "target_count": MAX_MATCH_SIZE})
            emit(
                "match_start",
                {
                    "player_id": player_id,
                    "target_count": len(STATE["players"]),
                    "world_width": WORLD_WIDTH,
                    "world_height": WORLD_HEIGHT,
                },
            )
            emit_world_state()
        else:
            emit("join_rejected", {"message": "This match is full. Try again after the next drop."})
        return
    if player_id not in STATE["lobby"]:
        STATE["lobby"][player_id] = create_player(player_id, request.sid)
    emit("joined_lobby", {"count": len(STATE["lobby"]), "target_count": MIN_MATCH_SIZE})
    emit("lobby_status", {"count": len(STATE["lobby"])})
    if not STATE["countdown_started"]:
        STATE["countdown_started"] = True
        socketio.start_background_task(lobby_start_timer)


@socketio.on("leave_lobby")
def handle_leave_lobby():
    player_id = session.get("player_id")
    if not player_id:
        return
    STATE["lobby"].pop(player_id, None)
    if player_id in STATE["players"]:
        STATE["players"].pop(player_id, None)
    emit("lobby_status", {"count": len(STATE["lobby"])})


@socketio.on("player_input")
def handle_player_input(data):
    player_id = session.get("player_id")
    player = STATE["players"].get(player_id) or STATE["lobby"].get(player_id)
    if not player:
        return
    player["input"] = {
        "up": bool(data.get("up", False)),
        "down": bool(data.get("down", False)),
        "left": bool(data.get("left", False)),
        "right": bool(data.get("right", False)),
    }


@socketio.on("open_chest")
def handle_open_chest():
    player_id = session.get("player_id")
    player = STATE["players"].get(player_id) or STATE["lobby"].get(player_id)
    if not player:
        return
    if len(player.get("extras", [])) >= 3:
        emit("toast", {"message": "Your pack is full. Use one of the extra options first."})
        return
    option = loot_option()
    if option in player["extras"]:
        alt_options = [name for name in OPTION_CATALOG if name not in BASE_OPTIONS and name not in player["extras"]]
        if alt_options:
            option = random.choice(alt_options)
    player["extras"].append(option)
    emit("toast", {"message": f"Chest opened! You gained {option}"})
    emit_world_state()


@socketio.on("battle_choice")
def handle_battle_choice(data):
    player_id = session.get("player_id")
    choice = data.get("choice")
    if not choice or STATE["battle"] is None:
        emit("battle_error", {"message": "The duel is no longer active. Try touching another player."})
        return
    if player_id not in STATE["players"] or STATE["players"][player_id]["sid"] != request.sid:
        player_id = next(
            (candidate_id for candidate_id, candidate in STATE["players"].items() if candidate["sid"] == request.sid),
            player_id,
        )
    if player_id not in STATE["battle"]["players"]:
        emit("battle_error", {"message": "This connection is not part of the active duel."})
        return
    player = STATE["players"].get(player_id)
    if not player or choice not in get_inventory(player):
        emit("battle_error", {"message": "That option is no longer in your inventory."})
        return
    STATE["battle"]["choices"][player_id] = choice
    emit("battle_choice_received", {"choice": choice})
    opponent_id = next(
        battle_player_id
        for battle_player_id in STATE["battle"]["players"]
        if battle_player_id != player_id
    )
    opponent = STATE["players"].get(opponent_id)
    if opponent and opponent["is_bot"] and opponent_id not in STATE["battle"]["choices"]:
        STATE["battle"]["choices"][opponent_id] = random.choice(get_inventory(opponent))
    if len(STATE["battle"]["choices"]) >= 2:
        resolve_battle()


@socketio.on("disconnect")
def handle_disconnect():
    player_id = session.get("player_id")
    if not player_id:
        return
    STATE["lobby"].pop(player_id, None)
    if player_id in STATE["players"]:
        STATE["players"].pop(player_id, None)
    if STATE["battle"] and player_id in STATE["battle"]["players"]:
        STATE["battle"] = None
    emit_world_state()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG") == "1"
    socketio.run(app, debug=debug, host="0.0.0.0", port=port)

