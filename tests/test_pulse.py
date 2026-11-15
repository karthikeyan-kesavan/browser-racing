import math
import unittest
from unittest.mock import patch

from flask import Flask
from flask_socketio import SocketIO

from game.pulse import Loadout, PulseRoom, register_pulse


class PulseSimulationTests(unittest.TestCase):
    def setUp(self):
        self.room = PulseRoom("ABC123")
        self.room.add("host", Loadout("HOST"))
        self.room.add("guest", Loadout("GUEST", ability="chain"))
        self.room.start()
        self.room.phase = "playing"
        self.room.launch = 0

    def test_targeted_parry_and_authoritative_speed_reset(self):
        host, guest = self.room.actors[:2]
        self.assertFalse(self.room.parry(guest))
        self.assertEqual(guest.cooldown, 0)
        self.room.ball.y = host.y - 35
        self.assertTrue(self.room.parry(host))
        self.room.tick(1 / 120)
        self.assertEqual(self.room.ball.speed, 261)
        self.assertEqual(host.perfects, 1)
        target = self.room.actors[self.room.ball.target]
        self.room.eliminate(target)
        self.room.eliminate(target)
        self.assertEqual(self.room.ball.speed, 225)
        self.assertEqual(self.room.earned[host.id], 20)
        self.assertEqual(host.kills, 1)
        self.assertEqual(self.room.ball.last_defender, -1)

    def test_chain_shield_and_freeze(self):
        guest = self.room.actors[1]
        self.assertTrue(self.room.ability(guest))
        self.assertEqual(self.room.ball.target, guest.id)
        self.assertFalse(self.room.parry(self.room.actors[0]))
        guest.ability = "shield"
        guest.ability_cooldown = 0
        self.assertTrue(self.room.ability(guest))
        self.room.ball.x, self.room.ball.y = guest.x, guest.y - 35
        self.room.tick(1 / 120)
        self.assertEqual(guest.shield, 0)
        self.assertEqual(guest.parries, 1)
        guest.ability = "freeze"
        guest.ability_cooldown = 0
        self.assertTrue(self.room.ability(guest))
        before = self.room.ball.snapshot()
        self.room.tick(.1)
        self.assertEqual(self.room.ball.snapshot(), before)

    def test_eliminated_human_spectates_and_win_rewards_are_once_only(self):
        self.room.eliminate(self.room.actors[1])
        self.assertEqual(self.room.phase, "playing")
        for bot in self.room.actors[2:]:
            self.room.ball.last_defender = 0
            self.room.eliminate(bot)
        self.assertEqual(self.room.phase, "result")
        self.assertEqual(self.room.winner, 0)
        self.assertEqual(self.room.earned[0], 140)
        self.assertEqual(self.room.victories[0], 1)
        self.room.eliminate(self.room.actors[5])
        self.assertEqual(self.room.earned[0], 140)


class PulseSocketTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["SECRET_KEY"] = "test-only"
        self.socketio = SocketIO(self.app, async_mode="threading")
        self.hub = register_pulse(self.socketio)
        self.background = patch.object(self.socketio, "start_background_task")
        self.background.start()
        self.addCleanup(self.background.stop)
        self.clients = []
        self.host = self.client()
        self.guest = self.client()
        self.loadout = {"name": "PLAYER", "color": "#69f3db", "model": "dragon", "ability": "dash"}
        self.created = self.command(self.host, "create", self.loadout)
        self.code = self.created["state"]["code"]
        self.command(self.guest, "join", {**self.loadout, "code": self.code.lower()})
        self.addCleanup(self.disconnect_clients)

    def client(self):
        client = self.socketio.test_client(self.app, namespace="/pulse")
        self.clients.append(client)
        return client

    def disconnect_clients(self):
        for client in self.clients:
            if client.is_connected("/pulse"):
                client.disconnect(namespace="/pulse")

    @staticmethod
    def command(client, command, data=None):
        return client.emit("pulse_command", {"command": command, "data": data},
                           namespace="/pulse", callback=True)

    def test_private_rooms_broadcast_only_to_their_members(self):
        stranger = self.client()
        other = self.command(stranger, "create", self.loadout)
        self.assertNotEqual(other["state"]["code"], self.code)
        self.assertFalse(self.command(self.guest, "start")["ok"])
        self.assertTrue(self.command(self.host, "start")["ok"])
        with patch.object(self.socketio, "emit") as broadcast:
            self.hub.tick(.1)
        broadcast.assert_called_once()
        event, frame = broadcast.call_args.args
        self.assertEqual(event, "pulse_state")
        self.assertEqual(frame["code"], self.code)
        self.assertEqual(sum(actor["isBot"] for actor in frame["actors"]), 4)
        self.assertEqual(broadcast.call_args.kwargs, {"namespace": "/pulse", "to": self.code})
        self.assertEqual(sum(code == self.code for code in self.hub.connections.values()), 2)
        self.assertFalse(self.command(stranger, "join", {**self.loadout, "code": self.code})["ok"])

    def test_sender_can_only_move_their_actor_and_inputs_are_validated(self):
        self.command(self.host, "start")
        room = self.hub.rooms[self.code]
        room.phase = "playing"
        room.launch = 10
        original_host = room.actors[0].x
        original_guest = room.actors[1].x
        self.assertTrue(self.command(self.guest, "input", {"x": 1, "y": 0, "facing": 0, "id": 0})["ok"])
        self.hub.tick(.1)
        self.assertEqual(room.actors[0].x, original_host)
        self.assertAlmostEqual(room.actors[1].x - original_guest, 17)
        for invalid in [float("nan"), float("inf"), True, 100, 10 ** 90]:
            self.assertFalse(self.command(self.guest, "input", {"x": invalid, "y": 0, "facing": 0})["ok"])
        self.assertFalse(self.command(self.guest, "action", {"action": "parry"})["ok"])
        self.assertFalse(self.command(self.guest, "loadout", self.loadout)["ok"])
        room.tick(.5)
        stopped = room.actors[1].x
        room.tick(.1)
        self.assertEqual(room.actors[1].x, stopped)
        self.assertLessEqual(math.hypot(room.actors[1].x, room.actors[1].y), 262)

    def test_host_disconnect_transfers_host_and_turns_contender_into_bot(self):
        self.command(self.host, "start")
        self.host.disconnect(namespace="/pulse")
        room = self.hub.rooms[self.code]
        self.assertTrue(room.actors[0].is_bot)
        self.assertEqual(room.members[room.host].slot, 1)
        self.guest.disconnect(namespace="/pulse")
        self.assertNotIn(self.code, self.hub.rooms)

    def test_join_requires_valid_code_available_slot_and_unstarted_round(self):
        invalid = self.client()
        self.assertFalse(self.command(invalid, "join", {**self.loadout, "code": "BAD"})["ok"])
        self.assertFalse(self.command(invalid, "join", {**self.loadout, "code": "ZZZZZZ"})["ok"])
        for _ in range(4):
            self.assertTrue(self.command(self.client(), "join", {**self.loadout, "code": self.code})["ok"])
        self.assertFalse(self.command(invalid, "join", {**self.loadout, "code": self.code})["ok"])
        self.command(self.host, "start")
        self.assertFalse(self.command(invalid, "join", {**self.loadout, "code": self.code})["ok"])


if __name__ == "__main__":
    unittest.main()
